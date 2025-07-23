# init_db.py

from sqlalchemy import create_engine
from app.models import db

# ❗️ 로컬 컴퓨터에서 프록시를 통해 접속하기 위한 최종 설정입니다.
DB_USER = "final_user"
DB_PASS = "Final_Password_123"
DB_NAME = "meetingapp_db"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

db_uri = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    print("Connecting to the database via proxy...")
    engine = create_engine(db_uri)
    
    print("Creating database tables...")
    db.metadata.create_all(engine)
    
    print("\n✅✅✅ SUCCESS! ✅✅✅")
    print("All database tables have been created successfully.")
    print("You can now close this window and the proxy window.")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
    print("Please check if the proxy is running and the database credentials are correct.")