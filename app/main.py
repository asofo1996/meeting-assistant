# app/main.py (최소 기능 버전)

from flask import Blueprint, render_template

# 데이터베이스 모델, 소켓 통신 등 모든 의존성을 제거합니다.
# from . import db, socketio
# from .models import AnswerStyle, Meeting, Transcript
# from .utils import get_openai_client

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """가장 기본적인 인덱스 페이지를 렌더링합니다."""
    # 데이터베이스 조회 없이 단순 템플릿만 반환합니다.
    return render_template('index.html')

@main.route('/health')
def health_check():
    """App Engine의 상태 확인을 위한 경로입니다."""
    return 'OK', 200

# 미팅 생성, 스타일 관리 등 다른 모든 라우트를 일시적으로 제거합니다.