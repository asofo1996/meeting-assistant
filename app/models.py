# app/models.py (수정된 최종 코드)

from . import db  # <<-- 이 부분이 가장 중요합니다. db = SQLAlchemy()를 삭제하고 이 코드로 변경합니다.
import datetime

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(
        db.String(100),
        nullable=False,
        default=lambda: f"Meeting {datetime.date.today().strftime('%Y-%m-%d')}"
    )
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    audio_file_path = db.Column(db.String(200), nullable=True)
    language = db.Column(db.String(10), nullable=False, default='en-US')
    transcripts = db.relationship('Transcript', backref='meeting', lazy=True, cascade="all, delete-orphan")

class Transcript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    gpt_response = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.Float, nullable=False)

class AnswerStyle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
