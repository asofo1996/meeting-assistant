# app/__init__.py

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO)
db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    logging.info("Application factory 'create_app' started.")

    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get('GCP_PROJECT', 'realtime-meeting-app-465901')

        # [⭐️핵심 수정⭐️] 비밀 ID를 원래의 'db-connection-string'으로 되돌립니다.
        secret_id = "db-connection-string"
        version_id = "latest"
        
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        logging.info(f"Attempting to access secret: {name}")
        
        response = secret_client.access_secret_version(request={"name": name})
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