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

    db_uri = os.environ.get('DATABASE_URI')
    if not db_uri:
        logging.error("CRITICAL FAILURE: DATABASE_URI environment variable is not set.")
        raise ValueError("DATABASE_URI environment variable is not set.")

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    logging.info("Successfully configured DB URI from environment variable.")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # [⭐️최종 수정⭐️] 앱 컨텍스트 안에서 데이터베이스 테이블을 생성합니다.
    # 이제 모든 연결 문제가 해결되었으므로, 이 코드가 정상적으로 실행되어 테이블을 생성합니다.
    with app.app_context():
        try:
            # models.py를 임포트하여 SQLAlchemy가 어떤 테이블을 만들지 알게 합니다.
            from . import models
            db.create_all()
            logging.info("Database tables created successfully (or already exist).")
        except Exception as e:
            logging.error(f"CRITICAL FAILURE: Could not create database tables. Error: {e}", exc_info=True)
            raise RuntimeError("Failed to create database tables") from e
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app