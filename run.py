from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Listen on all interfaces so the app can be reached from outside Docker or
    # a VM. Use 127.0.0.1 if you only need local access.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
