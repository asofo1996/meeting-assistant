# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from google.cloud import secretmanager

# 애플리케이션 전체에 적용될 로깅 설정
# Cloud Run이 로그를 더 잘 수집할 수 있도록 기본 설정을 사용합니다.
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    # --- [⭐️핵심 수정⭐️] ---
    # Secret Manager에서 DB 연결 정보를 가져오는 부분을 강화하고, 오류를 명확히 로깅합니다.
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        
        # Cloud Run 환경에서는 GCP_PROJECT 환경변수가 자동으로 설정됩니다.
        project_id = os.environ.get('GCP_PROJECT')
        if not project_id:
            # 로컬 환경 등에서 테스트를 위한 대체 프로젝트 ID
            project_id = 'realtime-meeting-app-465901'
            logging.warning(f"GCP_PROJECT env var not found. Using default: {project_id}")

        secret_id = "db-connection-string"
        version_id = "latest"
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        logging.info(f"Attempting to access secret: {name}")
        
        response = secret_client.access_secret_version(request={"name": name})
        db_uri = response.payload.data.decode("UTF-8")
        
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        logging.info("Successfully fetched and configured DB URI.")
        
    except Exception as e:
        # 이 부분이 가장 중요합니다. 오류 발생 시, 어떤 오류인지 정확히 로그에 남깁니다.
        logging.error(f"CRITICAL FAILURE: Could not configure database from Secret Manager. Error: {e}", exc_info=True)
        # 앱 시작을 의도적으로 실패시켜 Cloud Run에 문제가 있음을 명확히 알립니다.
        raise RuntimeError("Failed to configure database from Secret Manager") from e

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # DB 및 소켓 초기화
    db.init_app(app)
    
    # 블루프린트 등록
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Gunicorn의 gevent 워커와 함께 작동하려면 async_mode='gevent'가 필수입니다.
    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app