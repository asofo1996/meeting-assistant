# Dockerfile (최종 수정 버전)

# 1. 베이스 이미지를 'slim'이 아닌 완전한 버전으로 변경
FROM python:3.11

# 2. 환경 변수 설정
ENV PYTHONUNBUFFERED True

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 필요한 라이브러리 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 모든 프로젝트 파일 복사
COPY . .

# 6. 서버 실행 명령어 (이전과 동일)
CMD exec gunicorn --worker-class gevent -w 1 run:socketio
