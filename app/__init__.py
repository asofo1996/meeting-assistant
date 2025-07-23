# app/__init__.py

import os
from flask import Flask
from flask_socketio import SocketIO
from google.cloud import firestore

# Firestore 클라이언트를 초기화합니다.
# 특별한 설정 없이 자동으로 인증됩니다.
db = firestore.Client()

socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'a_very_secret_key'

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, async_mode='gevent')
    
    return app