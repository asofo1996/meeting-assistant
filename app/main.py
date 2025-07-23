# app/main.py

import os
import datetime
from flask import Blueprint, render_template, request, jsonify, current_app
from google.cloud import storage

# __init__.py에서 초기화된 firestore 클라이언트(db)와 socketio를 가져옵니다.
from . import db, socketio
from .utils import get_gpt_suggestion
from .speech_worker import SpeechWorker

main = Blueprint('main', __name__)

# 각 클라이언트(sid)에 대한 워커와 오디오 버퍼를 저장하는 딕셔너리
workers = {}
audio_buffers = {}

# ❗️ 중요: Cloud Storage에서 음성 파일을 저장할 버킷의 이름입니다.
# 이 이름으로 된 버킷이 프로젝트에 미리 생성되어 있어야 합니다.
# (예: my-meeting-app-final-audio-uploads)
GCS_BUCKET_NAME = f"{os.environ.get('GCP_PROJECT', 'my-meeting-app-final')}-audio-uploads"


def upload_audio_to_gcs(audio_data, meeting_id, sid):
    """메모리에 저장된 오디오 데이터를 GCS에 업로드합니다."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        # 각 녹음 세션에 대한 고유한 파일 이름을 생성합니다.
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        destination_blob_name = f"{meeting_id}/{sid}_{timestamp}.raw"
        
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(audio_data, content_type='audio/l16') # l16은 raw pcm 오디오를 의미
        
        current_app.logger.info(f"Audio for SID {sid} uploaded to {destination_blob_name}.")
        return blob.public_url
    except Exception as e:
        current_app.logger.error(f"GCS Upload failed for SID {sid}: {e}", exc_info=True)
        return None

# --- 라우팅 (Firestore 사용) ---

@main.route('/')
def index():
    """메인 페이지, 새 미팅을 생성합니다."""
    return render_template('index.html')

@main.route('/meeting/<string:meeting_id>')
def meeting_room(meeting_id):
    """미팅 룸, 실시간 음성 인식이 진행되는 곳입니다."""
    try:
        meeting_ref = db.collection('meetings').document(meeting_id)
        meeting_doc = meeting_ref.get()
        if not meeting_doc.exists:
            return "Meeting not found", 404
        meeting = meeting_doc.to_dict()

        styles_stream = db.collection('answer_styles').stream()
        styles = [doc.to_dict() for doc in styles_stream]

        transcripts_stream = db.collection('transcripts').where('meeting_id', '==', meeting_id).order_by('timestamp').stream()
        transcripts = [doc.to_dict() for doc in transcripts_stream]

        return render_template('meeting.html', meeting=meeting, styles=styles, transcripts=transcripts, meeting_id=meeting_id)
    except Exception as e:
        current_app.logger.error(f"Error loading meeting room {meeting_id}: {e}", exc_info=True)
        return "Internal Server Error", 500

@main.route('/history')
def history():
    """과거 미팅 기록을 보여줍니다."""
    try:
        meetings_stream = db.collection('meetings').order_by('created_at', direction='DESCENDING').stream()
        meetings = [doc.to_dict() for doc in meetings_stream]
        return render_template('history.html', meetings=meetings)
    except Exception as e:
        current_app.logger.error(f"Error fetching history: {e}", exc_info=True)
        return "Internal Server Error", 500

@main.route('/styles')
def styles():
    """답변 스타일을 관리합니다."""
    try:
        styles_stream = db.collection('answer_styles').stream()
        all_styles = [doc.to_dict() for doc in styles_stream]
        return render_template('styles.html', styles=all_styles)
    except Exception as e:
        current_app.logger.error(f"Error fetching styles: {e}", exc_info=True)
        return "Internal Server Error", 500

# --- API (Firestore 사용) ---

@main.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    """새로운 미팅을 생성하고 Firestore에 저장합니다."""
    try:
        data = request.get_json()
        language = data.get('language', 'en-US')
        
        doc_ref = db.collection('meetings').document()
        meeting_data = {
            'id': doc_ref.id,
            'language': language,
            'created_at': datetime.datetime.now(datetime.timezone.utc)
        }
        doc_ref.set(meeting_data)
        
        return jsonify({'meeting_id': doc_ref.id})
    except Exception as e:
        current_app.logger.error(f"Error creating meeting: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred while creating the meeting.'}), 500

@main.route('/api/style/create', methods=['POST'])
def create_style():
    """새로운 답변 스타일을 생성하고 Firestore에 저장합니다."""
    try:
        data = request.get_json()
        name, prompt = data.get('name'), data.get('prompt')
        if not name or not prompt:
            return jsonify({'success': False, 'message': 'Name and prompt are required.'}), 400
            
        doc_ref = db.collection('answer_styles').document()
        style_data = {
            'id': doc_ref.id,
            'name': name,
            'prompt': prompt
        }
        doc_ref.set(style_data)
        return jsonify({'success': True, 'id': doc_ref.id})
    except Exception as e:
        current_app.logger.error(f"Error creating style: {e}", exc_info=True)
        return jsonify({'success': False, 'message': 'An internal error occurred.'}), 500

# (이하 Delete API 및 Socket.IO 핸들러)

# --- Socket.IO 핸들러 (Firestore 및 GCS 사용) ---

@socketio.on('connect')
def handle_connect():
    current_app.logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in workers:
        workers[sid].close()
        del workers[sid]
    # 연결이 끊기면 녹음된 오디오를 업로드합니다.
    if sid in audio_buffers and audio_buffers[sid]['data']:
        audio_data = b''.join(audio_buffers[sid]['data'])
        meeting_id = audio_buffers[sid]['meeting_id']
        upload_audio_to_gcs(audio_data, meeting_id, sid)
        del audio_buffers[sid]
    current_app.logger.info(f"Client disconnected: {sid}")

@socketio.on('start_session')
def handle_start_session(data):
    sid = request.sid
    if sid in workers:
        current_app.logger.warning(f"Session already started for {sid}")
        return

    meeting_id = data.get('meeting_id')
    meeting_ref = db.collection('meetings').document(meeting_id)
    meeting = meeting_ref.get()
    if not meeting.exists:
        current_app.logger.error(f"Meeting {meeting_id} not found for session {sid}")
        return

    try:
        language_code = meeting.to_dict().get('language', 'en-US')
        worker = SpeechWorker(socketio, sid, language_code=language_code)
        workers[sid] = worker
        
        # 오디오 저장을 위한 버퍼를 초기화합니다.
        audio_buffers[sid] = {'data': [], 'meeting_id': meeting_id}
        
        socketio.start_background_task(worker.process)
        current_app.logger.info(f"Speech worker started for {sid} in meeting {meeting_id}")
    except Exception as e:
        current_app.logger.error(f"Failed to start speech worker for {sid}: {e}")

@socketio.on('audio_stream')
def handle_audio_stream(audio_data):
    sid = request.sid
    if sid in workers:
        workers[sid].add_audio_chunk(audio_data)
        # 오디오 데이터를 버퍼에 추가합니다.
        if sid in audio_buffers:
            audio_buffers[sid]['data'].append(audio_data)

@socketio.on('stop_session')
def handle_stop_session():
    sid = request.sid
    if sid in workers:
        workers[sid].close()
        del workers[sid]
        current_app.logger.info(f"Session stopped for {sid}")
    # 세션이 중지되면 녹음된 오디오를 업로드합니다.
    if sid in audio_buffers and audio_buffers[sid]['data']:
        audio_data = b''.join(audio_buffers[sid]['data'])
        meeting_id = audio_buffers[sid]['meeting_id']
        upload_audio_to_gcs(audio_data, meeting_id, sid)
        del audio_buffers[sid]

@socketio.on('final_transcript')
def handle_final_transcript_and_gpt(data):
    """최종 대화록을 Firestore에 저장하고 GPT 제안을 요청합니다."""
    sid = request.sid
    transcript_text = data.get('transcript')
    meeting_id = data.get('meeting_id')
    answer_style_id = data.get('answer_style_id')

    if not all([transcript_text, meeting_id, answer_style_id]):
        return

    try:
        # 1. 사용자 대화록을 Firestore에 저장합니다.
        user_transcript_ref = db.collection('transcripts').document()
        user_transcript_data = {
            'id': user_transcript_ref.id,
            'meeting_id': meeting_id,
            'speaker': 'Customer',
            'text': transcript_text,
            'timestamp': datetime.datetime.now(datetime.timezone.utc)
        }
        user_transcript_ref.set(user_transcript_data)
        
        # 2. 답변 스타일을 가져오고 GPT 제안을 요청합니다.
        style_ref = db.collection('answer_styles').document(answer_style_id)
        style_doc = style_ref.get()
        meeting_ref = db.collection('meetings').document(meeting_id)
        meeting_doc = meeting_ref.get()

        if style_doc.exists and meeting_doc.exists:
            style_prompt = style_doc.to_dict().get('prompt', '')
            language = meeting_doc.to_dict().get('language', 'en-US')
            
            suggestion = get_gpt_suggestion(transcript_text, style_prompt, language)
            socketio.emit('ai_response', {'text': suggestion}, to=sid)

            # 3. AI 응답을 Firestore에 저장합니다.
            ai_transcript_ref = db.collection('transcripts').document()
            ai_transcript_data = {
                'id': ai_transcript_ref.id,
                'meeting_id': meeting_id,
                'speaker': 'AI',
                'text': suggestion,
                'timestamp': datetime.datetime.now(datetime.timezone.utc)
            }
            ai_transcript_ref.set(ai_transcript_data)
            
    except Exception as e:
        current_app.logger.error(f"Error handling final transcript: {e}", exc_info=True)