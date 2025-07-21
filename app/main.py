import os
import time
from flask import Blueprint, render_template, request, jsonify, current_app
# from google.cloud import speech # 일시적으로 비활성화
from gevent.queue import Queue

from . import db, socketio
from .models import Meeting, Transcript, AnswerStyle
from .utils import get_openai_client, get_gpt_suggestion

main = Blueprint('main', __name__)

clients = {}

# --- 모든 페이지 라우팅과 API는 그대로 유지 ---
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

@main.route('/health')
def health_check():
    return 'OK', 200

@main.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    data = request.get_json()
    language = data.get('language', 'en-US')
    title = f"Meeting on {time.strftime('%Y-%m-%d')}"
    new_meeting = Meeting(title=title, language=language)
    db.session.add(new_meeting)
    db.session.commit()
    return jsonify({'meeting_id': new_meeting.id})

# --- 다른 모든 API 라우트도 그대로 유지 ---
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
    Transcript.query.filter_by(meeting_id=meeting_id).delete()
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({'success': True})


# --- 실시간 Socket.IO 통신 ---

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

# def transcription_worker(...):
#     """
#     백그라운드에서 음성 인식을 처리하는 워커 함수.
#     가장 유력한 충돌 원인이므로, 이 함수 전체를 일시적으로 주석 처리합니다.
#     """
#     pass

@socketio.on('connect')
def handle_connect():
    current_app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in clients:
        # clients[request.sid]['stream'].put(None) # 스트림도 비활성화
        del clients[request.sid]
    current_app.logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_session')
def handle_start_session(data):
    """
    클라이언트가 녹음 시작을 요청할 때, 백그라운드 작업 호출을 비활성화합니다.
    이렇게 하면 서버가 충돌하지 않고 최소한 실행 상태를 유지하는지 확인할 수 있습니다.
    """
    sid = request.sid
    if sid in clients:
        return
    
    clients[sid] = {} # 빈 딕셔너리로 클라이언트 상태만 유지
    
    # 'worker': socketio.start_background_task(...)
    # 문제의 핵심인 이 라인을 주석 처리합니다.

    current_app.logger.info(f"Session minimally started for {sid} (debug mode)")

@socketio.on('audio_stream')
def handle_audio_stream(audio_data):
    # 백그라운드 작업이 없으므로 아무것도 하지 않습니다.
    pass

@socketio.on('stop_session')
def handle_stop_session():
    sid = request.sid
    if sid in clients:
        del clients[sid]
        current_app.logger.info(f"Session stopped for {sid} (debug mode)")

@socketio.on('change_style')
def handle_change_style(data):
    sid = request.sid
    new_style_id = data.get('answer_style_id')
    current_app.logger.info(f"Client {sid} changed style to {new_style_id}")
