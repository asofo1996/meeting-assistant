from app import create_app, socketio

app = create_app(debug=False)

if __name__ == '__main__':
    # 로컬에서 실행 시 socketio.run 사용
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))