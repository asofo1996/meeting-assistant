# app/models.py

# from . import db -> 이 라인을 삭제합니다.
from datetime import datetime
from . import db # 이 라인을 유지합니다. (수정)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, default=f"Meeting on {datetime.now().strftime('%Y-%m-%d')}")
    language = db.Column(db.String(10), nullable=False, default='en-US')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transcripts = db.relationship('Transcript', backref='meeting', lazy=True, cascade="all, delete-orphan")

class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    speaker = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AnswerStyle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    