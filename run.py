# run.py (최종 수정본)

import eventlet
# 다른 모든 것을 임포트하기 전에 monkey_patch를 최상단에서 실행해야 합니다.
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # 이 부분은 로컬에서 python run.py로 실행할 때만 사용됩니다.
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)