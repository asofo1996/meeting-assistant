FROM python:3.11
ENV PYTHONUNBUFFERED True
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Gunicorn 대신, python 명령어로 worker.py를 직접 실행합니다.
CMD ["python", "worker.py"]