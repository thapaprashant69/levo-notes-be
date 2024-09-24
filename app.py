from flask import Flask, request, jsonify
from flask_mail import Mail
from flask_cors import CORS
from celery import Celery
from datetime import datetime
from models import db, Note
import pytz

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    mail.init_app(app)
    CORS(app)

    return app

app = create_app()

# Initialize database
with app.app_context():
    db.create_all()

# Create a Celery instance
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

#For adding tasks to celery
import tasks

# CRUD Endpoints for Note Management
@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    content = data.get('content')
    if not content:
        return jsonify({'error': 'Content is required'}), 400

    note = Note(content=content)
    db.session.add(note)
    db.session.commit()

    return jsonify({'id': note.id, 'content': note.content, 'created_at': note.created_at}), 201

@app.route('/notes', methods=['GET'])
def get_all_notes():
    notes = Note.query.all()
    notes_list = [{'id': note.id, 'content': note.content, 'created_at': note.created_at} for note in notes]
    return jsonify(notes_list), 200

@app.route('/notes/<string:id>', methods=['GET'])
def get_note(id):
    note = Note.query.get_or_404(id)
    return jsonify({'id': note.id, 'content': note.content, 'created_at': note.created_at})

@app.route('/notes/<string:id>', methods=['PUT'])
def update_note(id):
    note = Note.query.get_or_404(id)
    data = request.get_json()
    content = data.get('content')
    if content:
        note.content = content
        db.session.commit()

    return jsonify({'id': note.id, 'content': note.content})

@app.route('/notes/<string:id>', methods=['DELETE'])
def delete_note(id):    
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted'}), 204

@app.route('/notes/<string:id>', methods=['OPTIONS'])
def options_route(id):
    return '', 204

# Reminder Endpoint
@app.route('/notes/<string:id>/reminder', methods=['POST'])
async def schedule_reminder(id):
    from tasks import send_reminder_email
    note = Note.query.get_or_404(id)
    data = request.get_json()
    reminder_time_str = data.get('reminder_time')
    user_timezone_str = data.get('timezone')
    email = data.get('email')

    if not reminder_time_str or not email or not user_timezone_str:
        return jsonify({'error': 'Reminder time, email and timezone are required'}), 400

    reminder_time = datetime.fromisoformat(reminder_time_str)
    try:
        user_timezone = pytz.timezone(user_timezone_str)
    except pytz.UnknownTimeZoneError:
        return jsonify({'error':'Invalid timezone'}), 400
    
    localized_reminder_time = user_timezone.localize(reminder_time)
    utc_reminder_time = localized_reminder_time.astimezone(pytz.utc)

    note.reminder_time = utc_reminder_time
    db.session.commit()

    # Scheduling email asynchronously
    send_reminder_email.apply_async(args=[id, email], eta=utc_reminder_time)
    return jsonify({'message': 'Reminder scheduled'}), 200

if __name__ == '__main__':
    app.run(debug=True)
