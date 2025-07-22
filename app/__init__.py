# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import re # 정규표현식을 위한 모듈 임포트

logging.basicConfig(level=logging.INFO)
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    db_uri = os.environ.get('DATABASE_URI')
    if not db_uri:
        logging.error("CRITICAL FAILURE: DATABASE_URI environment variable is not set.")
        raise ValueError("DATABASE_URI environment variable is not set.")

    # [⭐️최종 진단 코드⭐️] Cloud Run이 실제로 어떤 URI를 받았는지 로그에 출력합니다.
    # (비밀번호는 보안을 위해 '*****'로 마스킹 처리됩니다.)
    masked_uri = re.sub(r':([^@]+)@', r':*****@', db_uri)
    logging.info(f"Cloud Run is attempting to connect with this URI: {masked_uri}")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app