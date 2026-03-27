import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.environ.get('DATABASE_URL')
if db_url and '@db:' in db_url:
    os.environ['DATABASE_URL'] = db_url.replace('@db:', '@localhost:')

from app import create_app, db
from app.models import User, Client, Service, TimeSlot, Appointment, ArchivedAppointment, NotaryPhoto

app = create_app()

with app.app_context():
    db.create_all()
    print("------------------------------------------")
    print("Успіх! Нова таблиця NotaryPhoto створена.")
    print("Всі старі дані збережено.")
    print("------------------------------------------")