import os
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

# (추가됨) Secret Manager 클라이언트를 임포트합니다.
from google.cloud import secretmanager

# .env 파일 로드 (로컬 개발 환경에서만 사용됨)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# 앱 전체에서 공유될 db, socketio 객체 생성
db = SQLAlchemy()
socketio = SocketIO()

def get_openai_api_key():
    """Secret Manager에서 OpenAI API 키를 가져오는 함수"""
    # Google Cloud 프로젝트 ID를 자동으로 가져옵니다.
    project_id = os.environ.get("GCP_PROJECT", None)
    if not project_id:
        # 로컬 환경 등에서 프로젝트 ID를 찾을 수 없는 경우
        # gcloud auth application-default print-access-token 명령 등으로 확인 가능
        # 또는 직접 하드코딩할 수 있습니다. (예: 'realtime-meeting-app-465901')
        # 이 부분은 배포 환경에서는 자동으로 설정되므로 크게 걱정하지 않아도 됩니다.
        try:
            import google.auth
            _, project_id = google.auth.default()
        except (ImportError, google.auth.exceptions.DefaultCredentialsError):
             print("로컬에서 GCP 프로젝트 ID를 찾을 수 없습니다.")
             return os.environ.get("OPENAI_API_KEY") # 로컬 .env 파일에서 키를 읽어옴


    secret_name = os.environ.get("OPENAI_API_KEY_SECRET_NAME")
    if not secret_name:
        return os.environ.get("OPENAI_API_KEY") # 로컬 .env 파일에서 키를 읽어옴

    client = secretmanager.SecretManagerServiceClient()
    
    # Secret 버전의 전체 경로를 구성합니다.
    resource_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    
    # Secret에 접근하여 값을 가져옵니다.
    response = client.access_secret_version(request={"name": resource_name})
    
    # Secret 값(API 키)을 반환합니다.
    return response.payload.data.decode("UTF-8")


def create_app():
    """Application Factory 함수"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # --- 데이터베이스 및 기타 설정 ---
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    
    if instance_connection_name:
        # Cloud SQL (배포 환경)
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql+pg8000://{db_user}:{db_pass}@/{db_name}"
            f"?unix_sock=/cloudsql/{instance_connection_name}/.s.PGSQL.5432"
        )
    else:
        # SQLite (로컬 개발 환경)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

    app.config['SECRET_KEY'] = 'your-very-secret-key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # (수정됨) Secret Manager에서 API 키를 가져와서 설정합니다.
    openai.api_key = get_openai_api_key()
    
    db.init_app(app)
    socketio.init_app(app, async_mode='gevent')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from . import models

    with app.app_context():
        db.create_all()

    return app
