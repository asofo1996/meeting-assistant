import os
from app import create_app

# FLASK_ENV 환경 변수를 확인하여 디버그 모드 설정
is_debug = os.environ.get('FLASK_ENV') == 'development'
app = create_app(debug=is_debug)

if __name__ == '__main__':
    # App Engine 환경에서는 gunicorn이 포트를 관리하지만,
    # 직접 실행을 위해 포트 설정을 추가합니다.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)