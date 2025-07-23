# Dockerfile

# Python 3.11 버전을 기반으로 이미지를 생성합니다.
FROM python:3.11-slim

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# 데이터베이스 연결 라이브러리 설치에 필요한 시스템 도구를 먼저 설치합니다.
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

# [⭐️최종 수정⭐️] Gunicorn 워커를 가장 표준적이고 안정적인 'gevent'로 변경합니다.
CMD ["gunicorn", "-b", ":$PORT", "-w", "1", "-k", "gevent", "app:create_app()"]