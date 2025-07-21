import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
socketio = SocketIO()

def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    # --- 최종 수정된 데이터베이스 설정 로직 ---
    # Google App Engine 환경인지 직접 확인
    if os.environ.get('GAE_ENV') == 'standard':
        # App Engine 환경일 경우 (Cloud SQL 사용)
        db_user = os.environ.get("DB_USER")
        db_pass = os.environ.get("DB_PASS")
        db_name = os.environ.get("DB_NAME")
        instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")

        # 만약 환경 변수가 없다면, 더 명확한 오류를 발생시킴
        if not all([db_user, db_pass, db_name, instance_connection_name]):
            raise ValueError("Database environment variables are not set in App Engine.")

        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}"
            f"?unix_sock=/cloudsql/{instance_connection_name}/.s.PGSQL.5432"
        )
    else:
        # 로컬 환경일 경우 (SQLite 사용)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetings.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        from . import main, models
        db.create_all()
        app.register_blueprint(main.main)
        return app
    