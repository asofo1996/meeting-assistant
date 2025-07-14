import os
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

# .env 파일 로드 (로컬 개발 환경에서만 사용됨)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# 앱 전체에서 공유될 db, socketio 객체 생성
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Application Factory 함수"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # --- (수정됨) Cloud SQL 데이터베이스 연결 설정 ---
    
    # app.yaml에 설정된 환경 변수들을 불러옵니다.
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    
    # Cloud SQL PostgreSQL에 연결하기 위한 데이터베이스 URI를 구성합니다.
    # 이전의 SQLite 설정은 이 코드로 완전히 대체됩니다.
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}"
        f"?unix_sock=/cloudsql/{instance_connection_name}/.s.PGSQL.5432"
    )
    
    # --- 나머지 설정 ---

    app.config['SECRET_KEY'] = 'your-very-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # OpenAI API 키 설정
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # 앱과 확장 기능들을 연결합니다.
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent')

    # Blueprint를 등록하여 라우팅을 활성화합니다.
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # 데이터베이스 모델을 임포트합니다.
    from . import models

    # 애플리케이션 컨텍스트 내에서 데이터베이스 테이블을 생성합니다.
    # 테이블이 이미 존재하면 아무 작업도 하지 않습니다.
    with app.app_context():
        db.create_all()

    return app
