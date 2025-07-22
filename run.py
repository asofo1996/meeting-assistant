# run.py

from app import create_app

# Application Factory를 호출하여 앱 인스턴스를 생성합니다.
app = create_app()

# 로컬 실행을 위한 부분
if __name__ == '__main__':
    app.run()
