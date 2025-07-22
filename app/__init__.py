# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

logging.basicConfig(level=logging.INFO)
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    # 환경변수에서 데이터베이스 URI를 읽어옵니다.
    db_uri = os.environ.get('DATABASE_URI')
    if not db_uri:
        logging.error("CRITICAL FAILURE: DATABASE_URI environment variable is not set.")
        raise ValueError("DATABASE_URI environment variable is not set.")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 데이터베이스를 앱에 연결합니다. (테이블 생성 코드는 완전히 제거되었습니다!)
    db.init_app(app)
    
    # 블루프린트를 등록합니다.
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # 소켓IO를 초기화합니다.
    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app