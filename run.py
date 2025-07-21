# run.py

import os
from app import create_app, socketio

# Application Factory를 호출하여 앱 인스턴스를 생성합니다.
app = create_app(debug=os.environ.get('FLASK_ENV') == 'development')

# 로컬 실행 및 Gunicorn entrypoint를 위해 남겨둡니다.
if __name__ == '__main__':
    socketio.run(app)
