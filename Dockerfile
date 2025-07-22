# Dockerfile (Web Server)
FROM python:3.11
ENV PYTHONUNBUFFERED True
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --log-level debug "app:create_app()"
