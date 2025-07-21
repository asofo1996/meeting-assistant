# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

# 1. 확장 객체를 먼저 생성합니다.
db = SQLAlchemy()
socketio = SocketIO()

def create_app(debug=False):
    """
    Application Factory: 앱을 생성하고, 확장 및 블루프린트를 등록합니다.
    """
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    # 2. 앱 설정을 구성합니다.
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

    # 3. 확장 객체를 앱에 등록합니다.
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent')

    with app.app_context():
        # 4. 블루프린트와 모델을 임포트하고 등록합니다.
        from . import main, models
        
        # db.create_all() # 이 라인은 주석 처리 상태를 유지합니다.

        app.register_blueprint(main.main)

        return app
    