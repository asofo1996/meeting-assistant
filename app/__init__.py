# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from google.cloud import secretmanager

# 애플리케이션 전체에 적용될 로깅 설정
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """Flask 애플리케이션을 생성하고 설정합니다."""
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    # Secret Manager에서 DB 연결 정보를 가져옵니다.
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        
        # Cloud Run 환경에서는 GCP_PROJECT 환경변수가 자동으로 설정됩니다.
        project_id = os.environ.get('GCP_PROJECT')
        if not project_id:
            project_id = 'realtime-meeting-app-465901'
            logging.warning(f"GCP_PROJECT env var not found. Using default: {project_id}")

        # [⭐️핵심 수정⭐️] secret_id를 사용자가 생성한 'openai-api-key'로 변경했습니다.
        secret_id = "openai-api-key"
        version_id = "latest"
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        logging.info(f"Attempting to access secret: {name}")
        
        response = secret_client.access_secret_version(request={"name": name})
        # 🚨 중요: 'openai-api-key' 보안 비밀의 값은 실제 DB 연결 문자열이어야 합니다.
        db_uri = response.payload.data.decode("UTF-8")
        
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        logging.info("Successfully fetched and configured DB URI.")
        
    except Exception as e:
        logging.error(f"CRITICAL FAILURE: Could not configure database from Secret Manager. Error: {e}", exc_info=True)
        raise RuntimeError("Failed to configure database from Secret Manager") from e

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app, async_mode='gevent')
    
    logging.info("Application creation finished successfully.")
    return app