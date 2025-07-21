import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# 데이터베이스와 소켓 객체 모두 생성
db = SQLAlchemy()
socketio = SocketIO()

def create_app(debug=False):
    """Create the final, full-featured application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    # --- 프로덕션 데이터베이스 설정 ---
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

    # 데이터베이스와 소켓 앱 초기화
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent')

    with app.app_context():
        from . import main, models
        # 첫 배포 이후에는 이 줄을 주석 처리하는 것이 좋습니다.
        db.create_all()
        app.register_blueprint(main.main)
        return app