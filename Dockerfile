# Python 3.11 버전을 기반으로 이미지를 생성합니다.
FROM python:3.11-slim

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# [⭐️핵심 수정⭐️] 데이터베이스 연결 라이브러리 설치에 필요한 시스템 도구를 먼저 설치합니다.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt를 먼저 복사하여 종속성을 설치합니다.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 소스 코드를 복사합니다.
COPY . .

# 컨테이너가 8080 포트를 통해 외부 요청을 수신하도록 설정합니다.
EXPOSE 8080

# Gunicorn 웹 서버를 실행하여 애플리케이션을 시작합니다.
# 디버그 로그 레벨을 추가하여 더 자세한 정보를 볼 수 있도록 합니다.
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --log-level debug "app:create_app()"