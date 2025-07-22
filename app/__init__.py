# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_socketio import SocketIO # SocketIO는 아직 주석 처리

# SQLAlchemy 객체만 생성
db = SQLAlchemy()
# socketio = SocketIO()

def create_app(debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    # --- 데이터베이스 설정만 복원 ---
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    db_uri = (
        f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}"
        f"?unix_sock=/cloudsql/{instance_connection_name}/.s.PGSQL.5432"
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 데이터베이스만 초기화
    db.init_app(app)

    with app.app_context():
        from . import main, models
        # 데이터베이스 테이블을 생성하는 코드를 다시 활성화합니다.
        db.create_all()
        app.register_blueprint(main.main)
        return app
