# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# 로깅 설정
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    # [⭐️핵심 수정⭐️] Secret Manager 접속 코드를 모두 삭제하고,
    # Cloud Run이 주입해 줄 환경변수에서 직접 데이터베이스 URI를 읽어옵니다.
    db_uri = os.environ.get('DATABASE_URI')
    if not db_uri:
        logging.error("CRITICAL FAILURE: DATABASE_URI environment variable is not set.")
        raise ValueError("DATABASE_URI environment variable is not set.")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    logging.info("Successfully configured DB URI from environment variable.")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app