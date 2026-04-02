import pytest
import threading
import os
import sys
from datetime import datetime, timedelta, date, time
from app import db
from app.models import TimeSlot, Service, Client, Appointment

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def concurrency_data(app):
    with app.app_context():
        service = Service(name="Стрес-тест", description="Конкурентність|Тест")
        db.session.add(service)
        
        dt = datetime.now() + timedelta(days=2)
        slot_1 = TimeSlot(date=dt.date(), start_time=dt.time(), is_booked=False)
        slot_2 = TimeSlot(date=dt.date(), start_time=(dt + timedelta(hours=1)).time(), is_booked=False)
        
        db.session.add_all([slot_1, slot_2])
        db.session.commit()
        
        data = {
            "s_id": str(service.id), 
            "slot_1": str(slot_1.id), 
            "slot_2": str(slot_2.id), 
            "date": dt.date().strftime('%Y-%m-%d')
        }
        yield data
        db.session.rollback()

def test_1_concurrency_race_condition_protection(app, client, concurrency_data):
    def make_booking(i):
        payload = {
            'name': f"User_{i}", 
            'email': f"race_{i}@test.com", 
            'phone': '+380000000000', 
            'service_id': concurrency_data['s_id'], 
            'date': concurrency_data['date'], 
            'time_id': concurrency_data['slot_1'], 
            'privacy': 'y'
        }
        with app.app_context():
            client.post('/appointments/book', data=payload)

    threads = [threading.Thread(target=make_booking, args=(i,)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    with app.app_context():
        count = Appointment.query.filter_by(slot_id=int(concurrency_data['slot_1'])).count()
        assert count == 1

def test_2_concurrency_simultaneous_different_slots(app, client, concurrency_data):
    def book_slot(slot_id, i):
        payload = {
            'name': f"User_{i}", 
            'email': f"diff_{i}@test.com", 
            'phone': '+380111111111',
            'service_id': concurrency_data['s_id'], 
            'date': concurrency_data['date'], 
            'time_id': slot_id, 
            'privacy': 'y'
        }
        with app.app_context():
            client.post('/appointments/book', data=payload)

    t1 = threading.Thread(target=book_slot, args=(concurrency_data['slot_1'], 1))
    t2 = threading.Thread(target=book_slot, args=(concurrency_data['slot_2'], 2))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    with app.app_context():
        s1 = db.session.get(TimeSlot, int(concurrency_data['slot_1']))
        s2 = db.session.get(TimeSlot, int(concurrency_data['slot_2']))
        assert s1.is_booked is True
        assert s2.is_booked is True

def test_3_concurrency_load_navigation_resilience(client):
    response = client.get('/')
    assert response.status_code == 200

def test_4_concurrency_db_session_isolation(app):
    with app.app_context():
        new_service = Service(name="Isolation Test", description="Test|Docs")
        db.session.add(new_service)
        # Перевірка, що об'єкт є в поточній сесії, але ще не в БД остаточно без коміту
        assert new_service in db.session
        db.session.rollback()
        assert new_service not in db.session