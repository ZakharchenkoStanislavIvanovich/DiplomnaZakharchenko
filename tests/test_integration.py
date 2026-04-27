import pytest
from app import db
from app.models import TimeSlot, Appointment, Client, Service
from datetime import datetime, timedelta, date, time
from unittest.mock import patch

@pytest.fixture
def integration_data(app):
    """Створює тимчасові дані, які зникнуть одразу після тесту"""
    with app.app_context():
        db.session.remove()
        
        service = Service(name="Експертна послуга", description="Тест|Опис")
        db.session.add(service)
        
        dt_base = datetime.now() + timedelta(days=5)
        slot_free = TimeSlot(date=dt_base.date(), start_time=dt_base.time(), is_booked=False)
        slot_busy = TimeSlot(date=dt_base.date(), start_time=(dt_base + timedelta(hours=1)).time(), is_booked=True)
        
        db.session.add_all([slot_free, slot_busy])
        db.session.flush()
        
        data = {
            "s_id": str(service.id), 
            "slot_id": str(slot_free.id), 
            "busy_id": str(slot_busy.id), 
            "date": dt_base.date().strftime('%Y-%m-%d')
        }
        
        yield data
        
        db.session.rollback()
        db.session.remove()

def test_1_successful_booking_logic(client, integration_data, app):
    """Перевірка логіки бронювання без фіксації в реальній БД"""
    payload = {
        'name': "Олексій", 
        'email': "int@test.com", 
        'phone': '+380990000001',
        'service_id': integration_data['s_id'], 
        'date': integration_data['date'], 
        'time_id': integration_data['slot_id'], 
        'privacy': 'y'
    }
    
    with patch('app.db.session.commit'):
        response = client.post('/appointments/book', data=payload)
        assert response.status_code in [200, 302]

def test_2_booking_conflict_management(client, integration_data):
    """Перевірка конфлікту (зайнятий слот)"""
    payload = {
        'name': "D", 'email': "c@t.com", 'phone': '+380990000002', 
        'service_id': integration_data['s_id'], 'date': integration_data['date'], 
        'time_id': integration_data['busy_id'], 'privacy': 'y'
    }
    response = client.post('/appointments/book', data=payload, follow_redirects=True)
    assert b"success" not in response.data.lower()

def test_3_api_available_slots_filtering(client, integration_data):
    """Перевірка API фільтрації слотів"""
    response = client.get(f"/appointments/available_times?date={integration_data['date']}")
    data = response.get_data(as_text=True)
    assert integration_data['slot_id'] in data
    assert integration_data['busy_id'] not in data

def test_4_ui_form_rendering(client):
    """Перевірка відображення форми (чисто візуальний тест)"""
    response = client.get('/appointments/book')
    assert response.status_code == 200
    assert b'name' in response.data

def test_5_data_encryption_cycle_in_session(app):
    """Перевірка шифрування в межах однієї сесії пам'яті"""
    with app.app_context():
        test_client = Client(name="Степан Тестовий", email="stepan@test.com", phone="777")
        db.session.add(test_client)
        db.session.flush()
        
        assert test_client._name.startswith("gAAAAA")
        assert test_client.name == "Степан Тестовий"
        
        db.session.rollback()

def test_6_api_past_date_empty(client):
    """Перевірка запиту на минулу дату"""
    response = client.get("/appointments/available_times?date=2020-01-01")
    assert response.get_json() == []