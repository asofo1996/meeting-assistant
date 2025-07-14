from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # eventlet 서버를 사용하여 앱을 실행합니다.
    # debug=True는 자동 재실행 기능을 활성화합니다.
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)