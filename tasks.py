from celery import Celery
from flask_mail import Message
from app import mail, create_app
from models import Note

app = create_app()
celery = Celery(__name__, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@celery.task
def send_reminder_email(note_id, email):
    with app.app_context():
        note = Note.query.get(note_id)
        if note:
            msg = Message(f"Reminder for Note {note.id}",
                          recipients=[email],
                          body=f"Reminder for your note: {note.content} scheduled for UTC{note.reminder_time}")
            mail.send(msg)
