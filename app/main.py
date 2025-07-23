# app/main.py

import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app
from sqlalchemy import text # ⭐️ 최종 진단을 위해 추가
from . import db, socketio
from .models import Meeting, Transcript, AnswerStyle
from .utils import get_gpt_suggestion
from .speech_worker import SpeechWorker

main = Blueprint('main', __name__)

workers = {}

# --- [⭐️ 최종 진단 코드 ⭐️] ---
@main.route('/db-test')
def db_test():
    """데이터베이스 연결을 테스트하기 위한 가장 간단한 엔드포인트."""
    try:
        # 가장 기본적인 쿼리를 실행하여 연결을 테스트합니다.
        result = db.session.execute(text('SELECT 1')).scalar()
        if result == 1:
            return jsonify({'status': 'success', 'message': 'Database connection is OK!'}), 200
        else:
            return jsonify({'status': 'failure', 'message': f'Query returned unexpected result: {result}'}), 500
    except Exception as e:
        # 오류 발생 시, 어떤 오류인지 명확하게 보여줍니다.
        current_app.logger.error(f"Database connection test failed: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
# ------------------------------------


# --- 기존 라우팅 (이하 코드는 그대로) ---
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/meeting/<int:meeting_id>')
def meeting_room(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    styles = AnswerStyle.query.all()
    transcripts = Transcript.query.filter_by(meeting_id=meeting_id).order_by(Transcript.timestamp).all()
    return render_template('meeting.html', meeting=meeting, styles=styles, transcripts=transcripts, meeting_id=meeting_id)

@main.route('/history')
def history():
    meetings = Meeting.query.order_by(Meeting.created_at.desc()).all()
    return render_template('history.html', meetings=meetings)

@main.route('/styles')
def styles():
    all_styles = AnswerStyle.query.all()
    return render_template('styles.html', styles=all_styles)

@main.route('/health')
def health_check():
    return 'OK', 200

# --- API ---
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
    name, prompt = data.get('name'), data.get('prompt')
    if not name or not prompt:
        return jsonify({'success': False, 'message': 'Name and prompt are required.'}), 400
    new_style = AnswerStyle(name=name, prompt=prompt)
    db.session.add(new_style)
    db.session.commit()
    return jsonify({'success': True, 'id': new_style.id})

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

# --- Socket.IO ---
@socketio.on('connect')
def handle_connect():
    current_app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in workers:
        workers[sid].close()
        del workers[sid]
    current_app.logger.info(f"Client disconnected: {sid}")

@socketio.on('start_session')
def handle_start_session(data):
    sid = request.sid
    if sid in workers:
        current_app.logger.warning(f"Session already started for {sid}")
        return

    meeting_id = data.get('meeting_id')
    meeting = Meeting.query.get(meeting_id)
    if not meeting:
        current_app.logger.error(f"Meeting {meeting_id} not found for session {sid}")
        return

    try:
        worker = SpeechWorker(socketio, sid, language_code=meeting.language)
        workers[sid] = worker
        socketio.start_background_task(worker.process)
        current_app.logger.info(f"Speech worker started for {sid} in meeting {meeting_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to start speech worker for {sid}: {e}")

@socketio.on('audio_stream')
def handle_audio_stream(audio_data):
    sid = request.sid
    if sid in workers:
        workers[sid].add_audio_chunk(audio_data)

@socketio.on('stop_session')
def handle_stop_session():
    sid = request.sid
    if sid in workers:
        workers[sid].close()
        del workers[sid]
        current_app.logger.info(f"Session stopped for {sid}")

@socketio.on('final_transcript')
def handle_gpt_suggestion(data):
    sid = request.sid
    transcript = data.get('transcript')

    answer_style_id = data.get('answer_style_id')
    meeting_id = data.get('meeting_id')
    
    answer_style = AnswerStyle.query.get(answer_style_id)
    meeting = Meeting.query.get(meeting_id)

    if not transcript or not answer_style or not meeting:
        return

    try:
        suggestion = get_gpt_suggestion(transcript, answer_style.prompt, meeting.language)
        socketio.emit('ai_response', {'text': suggestion}, to=sid)
        current_app.logger.info(f"Sent AI suggestion to {sid}")

        new_transcript = Transcript(
            meeting_id=meeting.id,
            speaker='Customer',
            text=transcript
        )
        ai_transcript = Transcript(
            meeting_id=meeting.id,
            speaker='AI',
            text=suggestion
        )
        db.session.add(new_transcript)
        db.session.add(ai_transcript)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(f"Error getting GPT suggestion or saving transcript: {e}")