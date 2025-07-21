from flask import Blueprint, render_template, request, jsonify
from . import db
from .models import Meeting

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/health')
def health_check():
    """App Engine a readiness check."""
    return 'OK', 200

# 데이터베이스를 사용하는 API 라우트 복원
@main.route('/api/meeting/create', methods=['POST'])
def create_meeting():
    data = request.get_json()
    language = data.get('language', 'en-US')
    new_meeting = Meeting(language=language)
    db.session.add(new_meeting)
    db.session.commit()
    return jsonify({'meeting_id': new_meeting.id})