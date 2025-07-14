import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app
from google.cloud import speech
from gevent.queue import Queue # <<< 이 부분이 eventlet에서 gevent로 변경되었습니다.

from . import db, socketio
from .models import Meeting, Transcript, AnswerStyle
from .utils import get_gpt_suggestion

main = Blueprint('main', __name__)

clients = {}

# --- 1. 페이지 라우팅 ---
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/meeting/<int:meeting_id>')
def meeting_room(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    styles = AnswerStyle.query.all()
    transcripts = Transcript.query.filter_by(meeting_id=meeting_id).order_by(Transcript.timestamp).all()
    return render_template('meeting.html', meeting=meeting, styles=styles, transcripts=transcripts)

@main.route('/history')
def history():
    meetings = Meeting.query.order_by(Meeting.created_at.desc()).all()
    return render_template('history.html', meetings=meetings)

@main.route('/styles')
def styles():
    all_styles = AnswerStyle.query.all()
    return render_template('styles.html', styles=all_styles)


# --- 2. API 엔드포인트 ---
@main.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    data = request.get_json()
    language = data.get('language', 'en-US')
    new_meeting = Meeting(language=language)
    db.session.add(new_meeting)
    db.session.commit()
    return jsonify({'meeting_id': new_meeting.id})

@main.route('/api/style/create', methods=['POST'])
def create_style():
    data = request.get_json()
    name = data.get('name')
    prompt = data.get('prompt')
    if not name or not prompt:
        return jsonify({'success': False, 'message': 'Name and prompt are required.'}), 400
    if AnswerStyle.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'A style with this name already exists.'}), 400
    new_style = AnswerStyle(name=name, prompt=prompt)
    db.session.add(new_style)
    db.session.commit()
    return jsonify({'success': True, 'id': new_style.id, 'name': new_style.name, 'prompt': new_style.prompt})

@main.route('/api/style/delete/<int:style_id>', methods=['DELETE'])
def delete_style(style_id):
    style = AnswerStyle.query.get_or_404(style_id)
    db.session.delete(style)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/meeting/delete/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({'success': True})


# --- 3. 실시간 SocketIO 통신 ---
@socketio.on('connect')
def handle_connect():
    current_app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    current_app.logger.info(f"Client disconnected: {request.sid}")
    if request.sid in clients:
        del clients[request.sid]

@socketio.on('start_transcription')
def handle_start_transcription(data):
    app = current_app._get_current_object()
    sid = request.sid
    clients[sid] = {'audio_queue': Queue()}
    meeting_id = data.get('meeting_id')
    language_code = data.get('language', 'en-US')
    clients[sid]['language'] = language_code
    clients[sid]['style_id'] = data.get('style_id')
    current_app.logger.info(f"[{sid}] Starting transcription for meeting {meeting_id} in {language_code}")
    speech_client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )
    def audio_generator(sid):
        q = clients.get(sid, {}).get('audio_queue')
        if not q: return
        while True:
            chunk = q.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)
    
    try:
        current_app.logger.info(f"[{sid}] Google speech_client.streaming_recognize 호출 시도...")
        responses = speech_client.streaming_recognize(
            config=streaming_config, requests=audio_generator(sid)
        )
        current_app.logger.info(f"[{sid}] Google speech_client.streaming_recognize 호출 성공. 응답 대기 시작.")
    except Exception as e:
        current_app.logger.error(f"[{sid}] streaming_recognize 호출 중 즉시 오류 발생: {e}", exc_info=True)
        return

    socketio.start_background_task(target=process_responses, app=app, sid=sid, responses=responses, meeting_id=meeting_id)

def process_responses(app, sid, responses, meeting_id):
    with app.app_context():
        current_app.logger.info(f"[{sid}] Google 응답 처리 시작. 루프 진입 대기 중...")
        try:
            for i, response in enumerate(responses):
                current_app.logger.info(f"[{sid}] Google로부터 {i+1}번째 응답 수신: {response}")
                
                if not response.results: continue
                result = response.results[0]
                if not result.alternatives: continue
                
                transcript = result.alternatives[0].transcript
                socketio.emit('transcript_update', {'transcript': transcript, 'is_final': result.is_final}, room=sid)

                if result.is_final and transcript.strip():
                    state = clients.get(sid)
                    if not state: break
                    style = AnswerStyle.query.get(state['style_id'])
                    style_prompt = style.prompt if style else "Be a helpful assistant."
                    socketio.start_background_task(
                        target=process_final_transcript, 
                        app=app, sid=sid, meeting_id=meeting_id, 
                        transcript=transcript, style_prompt=style_prompt, language=state['language']
                    )
        except Exception as e:
            current_app.logger.error(f"[{sid}] Google 응답 처리 중 심각한 오류 발생: {e}", exc_info=True)
        finally:
            current_app.logger.info(f"[{sid}] Google 응답 처리 루프 종료.")

@socketio.on('audio_stream')
def handle_audio_stream(payload):
    sid = request.sid
    if sid in clients:
        q = clients[sid].get('audio_queue')
        if q and q.qsize() < 50:
            audio_data = payload['data']
            q.put(audio_data)

@socketio.on('stop_transcription')
def handle_stop_transcription(data):
    sid = request.sid
    current_app.logger.info(f"[{sid}] Stopping transcription.")
    if sid in clients and 'audio_queue' in clients[sid]:
        clients[sid]['audio_queue'].put(None)

@socketio.on('change_style')
def change_style(data):
    sid = request.sid
    style_id = data.get('style_id')
    if sid in clients:
        clients[sid]['style_id'] = style_id
        current_app.logger.info(f"[{sid}] Changed style to {style_id}")
        socketio.emit('style_changed_ack', {'message': 'Style updated successfully.'}, room=sid)

def process_final_transcript(app, sid, meeting_id, transcript, style_prompt, language):
    timestamp = time.time()
    gpt_response = get_gpt_suggestion(transcript, style_prompt, language)
    with app.app_context():
        new_transcript = Transcript(
            meeting_id=meeting_id,
            text=transcript,
            gpt_response=gpt_response,
            timestamp=timestamp
        )
        db.session.add(new_transcript)
        db.session.commit()
        transcript_id = new_transcript.id
    socketio.emit('final_result', {
        'transcript_id': transcript_id,
        'text': transcript,
        'gpt_response': gpt_response
    }, room=sid)