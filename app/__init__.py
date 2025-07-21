# app/__init__.py (최소 기능 버전)

from flask import Flask

# 모든 복잡한 라이브러리 초기화를 제거합니다.
# from flask_sqlalchemy import SQLAlchemy
# from flask_socketio import SocketIO
# db = SQLAlchemy()
# socketio = SocketIO()

def create_app(debug=False):
    """Create a minimal application for debugging."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    # 데이터베이스, 소켓 등 모든 초기화를 제거합니다.
    # db.init_app(app)
    # socketio.init_app(app)

    with app.app_context():
        # main 블루프린트만 등록합니다.
        from . import main
        app.register_blueprint(main.main)
        return app