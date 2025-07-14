# app/__init__.py (수정된 최종 코드)

import os
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

# .env 파일 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# 앱 전체에서 공유될 db, socketio 객체 생성
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Application Factory 함수"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # 환경 변수에서 설정값 로드
    app.config['SECRET_KEY'] = 'your-very-secret-key' 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # OpenAI API 키 설정
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # app과 확장(db, socketio)을 연결
    db.init_app(app)
    socketio.init_app(app, async_mode='eventlet')

    # Blueprint 등록
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # 모델 임포트
    from . import models

    # 애플리케이션 컨텍스트 내에서 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()

    return app