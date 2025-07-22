# init_db.py

import os
from sqlalchemy import create_engine
from app.models import db  # 우리의 모델과 db 객체를 가져옵니다.

# ❗️ 중요: 이 스크립트는 로컬 컴퓨터에서 실행할 것이므로,
# Secret Manager가 아닌, 직접 입력한 연결 정보를 사용합니다.
# 사용자와 데이터베이스 이름은 이전 단계에서 만든 것을 사용합니다.
DB_USER = "final_user"
DB_PASS = "Final_Password_123"
DB_NAME = "final_db"
INSTANCE_CONNECTION_NAME = "realtime-meeting-app-465901:asia-northeast3:meeting-db"

# 데이터베이스 연결 문자열
db_uri = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@/{DB_NAME}?host=/cloudsql/{INSTANCE_CONNECTION_NAME}"

try:
    print("Connecting to the database...")
    engine = create_engine(db_uri)
    
    # 데이터베이스에 모든 테이블을 생성합니다.
    print("Creating database tables...")
    db.metadata.create_all(engine)
    
    print("✅ Database tables created successfully!")

except Exception as e:
    print(f"❌ An error occurred: {e}")