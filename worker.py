import os
import ast
import time
import threading
from flask import Flask
from google.cloud import pubsub_v1, speech

from app import create_app, db
from app.models import Transcript, AnswerStyle
from app.utils import get_gpt_suggestion

# 1. Flask 앱 객체를 먼저 생성합니다.
app = Flask(__name__)

# --- Pub/Sub 설정 ---
project_id = os.environ.get("GCP_PROJECT")
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()
start_subscription_path = subscriber.subscription_path(project_id, 'start-transcription-sub')
results_topic_path = publisher.topic_path(project_id, 'transcription-results-topic')

# 데이터베이스 사용을 위한 Flask 앱 컨텍스트 생성
flask_app = create_app()
app_context = flask_app.app_context()

@app.route('/')
def health_check():
    """Cloud Run이 이 경로를 확인하여 서비스가 살아있는지 판단합니다."""
    return "Worker is running.", 200

def process_transcription(data):
    """실제 음성 분석을 수행하는 핵심 로직 (이전과 동일)"""
    # ... (이전 답변의 process_transcription 함수 내용을 여기에 붙여넣으세요) ...
    print(f"Processing transcription for sid: {data['sid']}")
    time.sleep(15) # 시뮬레이션
    final_result = f"최종 분석 결과 for {data['sid']}"
    with app_context:
        new_transcript = Transcript(meeting_id=data['meeting_id'], speaker='customer', text=final_result)
        db.session.add(new_transcript)
        db.session.commit()
    publisher.publish(results_topic_path, final_result.encode('utf-8'), event='final_transcript', sid=data['sid'])

def message_callback(message):
    """Pub/Sub 메시지를 받았을 때 실행되는 함수 (이전과 동일)"""
    try:
        data = ast.literal_eval(message.data.decode('utf-8'))
        process_transcription(data)
        message.ack()
    except Exception as e:
        print(f"Error processing message: {e}")

def start_subscriber():
    """Pub/Sub 메시지를 무한 대기하며 듣는 함수"""
    streaming_pull_future = subscriber.subscribe(start_subscription_path, callback=message_callback)
    print(f"Listening for messages on {start_subscription_path}...")
    try:
        streaming_pull_future.result()
    except Exception as e:
        print(f"Subscriber stopped: {e}")
        streaming_pull_future.cancel()

if __name__ == '__main__':
    # 2. Pub/Sub 리스너를 별도의 '백그라운드 스레드'에서 시작합니다.
    subscriber_thread = threading.Thread(target=start_subscriber, daemon=True)
    subscriber_thread.start()

    # 3. 메인 스레드에서는 Cloud Run을 만족시키기 위한 웹 서버를 실행합니다.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)