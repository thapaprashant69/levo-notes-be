from flask_sqlalchemy import SQLAlchemy
import datetime
import uuid

db = SQLAlchemy()

class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    reminder_time = db.Column(db.DateTime, nullable=True)
