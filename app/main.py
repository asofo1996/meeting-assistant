import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app
from google.cloud import speech
from gevent.queue import Queue

from . import db, socketio
from .models import Meeting, Transcript, AnswerStyle
from .utils import get_openai_client, get_gpt_suggestion

main = Blueprint('main', __name__)

# 클라이언트별 스트림을 관리하기 위한 딕셔너리
clients = {}

# --- 1. 페이지 라우팅 ---

@main.route('/')
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template('index.html')

@main.route('/meeting/<int:meeting_id>')
def meeting_room(meeting_id):
    """미팅룸 페이지를 렌더링합니다."""
    meeting = Meeting.query.get_or_404(meeting_id)
    styles = AnswerStyle.query.all()
    transcripts = Transcript.query.filter_by(meeting_id=meeting_id).order_by(Transcript.timestamp).all()
    return render_template('meeting.html', meeting=meeting, styles=styles, transcripts=transcripts)

@main.route('/history')
def history():
    """과거 미팅 기록 페이지를 렌더링합니다."""
    meetings = Meeting.query.order_by(Meeting.created_at.desc()).all()
    return render_template('history.html', meetings=meetings)

@main.route('/styles')
def styles():
    """답변 스타일 관리 페이지를 렌더링합니다."""
    all_styles = AnswerStyle.query.all()
    return render_template('styles.html', styles=all_styles)

@main.route('/health')
def health_check():
    """App Engine의 준비 상태 확인(readiness check)을 위한 경로입니다."""
    return 'OK', 200


# --- 2. API 엔드포인트 ---

@main.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    """새로운 미팅을 생성하고 ID를 반환합니다."""
    data = request.get_json()
    language = data.get('language', 'en-US')

    # 미팅 제목을 생성 (예: "Meeting on 2025-07-22")
    title = f"Meeting on {time.strftime('%Y-%m-%d')}"
    new_meeting = Meeting(title=title, language=language)

    db.session.add(new_meeting)
    db.session.commit()
    return jsonify({'meeting_id': new_meeting.id})

@main.route('/api/style/create', methods=['POST'])
def create_style():
    """새로운 답변 스타일을 생성합니다."""
    data = request.get_json()
    name, prompt = data.get('name'), data.get('prompt')
    if not name or not prompt:
        return jsonify({'success': False, 'message': 'Name and prompt are required.'}), 400

    new_style = AnswerStyle(name=name, prompt=prompt)
    db.session.add(new_style)
    db.session.commit()
    return jsonify({'success': True, 'id': new_style.id})

@main.route('/api/style/delete/<int:style_id>', methods=['DELETE'])
def delete_style(style_id):
    """기존 답변 스타일을 삭제합니다."""
    style = AnswerStyle.query.get_or_404(style_id)
    db.session.delete(style)
    db.session.commit()
    return jsonify({'success': True})

@main.route('/api/meeting/delete/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    """과거 미팅 기록을 삭제합니다."""
    meeting = Meeting.query.get_or_404(meeting_id)
    Transcript.query.filter_by(meeting_id=meeting_id).delete()
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({'success': True})


# --- 3. 실시간 Socket.IO 통신 ---

class AudioStream:
    """오디오 스트림을 관리하는 클래스."""
    def __init__(self):
        self.queue = Queue()

    def __call__(self):
        while True:
            chunk = self.queue.get()
            if chunk is None:
                return
            yield chunk

    def put(self, data):
        self.queue.put(data)

def transcription_worker(stream, sid, meeting_id, language_code, answer_style_id):
    """백그라운드에서 음성 인식을 처리하는 워커 함수."""
    app = current_app._get_current_object()
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
        enable_automatic_punctuation=True
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    try:
        requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in stream())
        responses = client.streaming_recognize(streaming_config, requests)

        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if result.is_final:
                with app.app_context():
                    current_app.logger.info(f"Final Transcript for {sid}: {transcript}")
                    new_transcript = Transcript(
                        meeting_id=meeting_id,
                        speaker='customer',
                        text=transcript
                    )
                    db.session.add(new_transcript)
                    db.session.commit()

                    socketio.emit('final_transcript', {'transcript': transcript}, room=sid)

                    style = AnswerStyle.query.get(answer_style_id)
                    prompt = style.prompt if style else "Answer professionally."
                    suggestion = get_gpt_suggestion(transcript, prompt)
                    socketio.emit('ai_response', {'text': suggestion}, room=sid)
            else:
                socketio.emit('interim_transcript', {'transcript': transcript}, room=sid)

    except Exception as e:
        current_app.logger.error(f"Transcription worker error for {sid}: {e}")
    finally:
        current_app.logger.info(f"Transcription worker for {sid} finished.")


@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시 호출됩니다."""
    current_app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 종료 시 호출됩니다."""
    if request.sid in clients:
        clients[request.sid]['stream'].put(None)
        del clients[request.sid]
    current_app.logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_session')
def handle_start_session(data):
    """클라이언트가 녹음 시작을 요청할 때 호출됩니다."""
    sid = request.sid
    meeting_id = data.get('meeting_id')
    language_code = data.get('language_code', 'en-US')
    answer_style_id = data.get('answer_style_id')

    if sid in clients:
        current_app.logger.warning(f"Session already started for {sid}")
        return

    stream = AudioStream()
    clients[sid] = {
        'stream': stream,
        'worker': socketio.start_background_task(
            transcription_worker, stream, sid, meeting_id, language_code, answer_style_id
        )
    }
    current_app.logger.info(f"Started session for {sid}, Meeting ID: {meeting_id}")

@socketio.on('audio_stream')
def handle_audio_stream(audio_data):
    """클라이언트로부터 오디오 데이터를 받았을 때 호출됩니다."""
    if request.sid in clients:
        clients[request.sid]['stream'].put(audio_data)

@socketio.on('stop_session')
def handle_stop_session():
    """클라이언트가 녹음 종료를 요청할 때 호출됩니다."""
    sid = request.sid
    if sid in clients:
        clients[sid]['stream'].put(None)
        del clients[sid]
        current_app.logger.info(f"Stopped session for {sid}")

@socketio.on('change_style')
def handle_change_style(data):
    """답변 스타일 변경 시 호출됩니다 (현재 구현에서는 직접적인 영향 없음)."""
    sid = request.sid
    new_style_id = data.get('answer_style_id')
    current_app.logger.info(f"Client {sid} changed style to {new_style_id}")
