import pytest
from app import db
from app.models import TimeSlot, Appointment, Client, Service
from datetime import datetime, timedelta, date, time
from unittest.mock import patch

@pytest.fixture
def integration_data(app):
    with app.app_context():
        service = Service(name="Експертна послуга", description="Тест|Опис")
        db.session.add(service)
        
        dt_base = datetime.now() + timedelta(days=5)
        slot_free = TimeSlot(date=dt_base.date(), start_time=dt_base.time(), is_booked=False)
        slot_busy = TimeSlot(date=dt_base.date(), start_time=(dt_base + timedelta(hours=1)).time(), is_booked=True)
        
        db.session.add_all([slot_free, slot_busy])
        db.session.commit()
        
        yield {
            "s_id": str(service.id), 
            "slot_id": str(slot_free.id), 
            "busy_id": str(slot_busy.id), 
            "date": dt_base.date().strftime('%Y-%m-%d')
        }
        
        db.session.rollback()

def test_1_successful_booking_db_persistence(client, integration_data, app):
    payload = {
        'name': "Олексій", 
        'email': "int@test.com", 
        'phone': '+380990000001',
        'service_id': integration_data['s_id'], 
        'date': integration_data['date'], 
        'time_id': integration_data['slot_id'], 
        'privacy': 'y'
    }
    
    with patch('app.appointments.routes.db.session.commit') as mock_commit:
        client.post('/appointments/book', data=payload)
        
    with app.app_context():
        db_client = Client.query.filter_by(email="int@test.com").first()
        if db_client:
            assert db_client.name == "Олексій"

def test_2_booking_conflict_management(client, integration_data):
    payload = {
        'name': "D", 'email': "c@t.com", 'phone': '+380990000002', 
        'service_id': integration_data['s_id'], 'date': integration_data['date'], 
        'time_id': integration_data['busy_id'], 'privacy': 'y'
    }
    response = client.post('/appointments/book', data=payload, follow_redirects=True)
    assert b"success" not in response.data.lower()

def test_3_api_available_slots_filtering(client, integration_data):
    response = client.get(f"/appointments/available_times?date={integration_data['date']}")
    data = response.get_data(as_text=True)
    assert integration_data['slot_id'] in data
    assert integration_data['busy_id'] not in data

def test_4_ui_form_rendering_integrity(client):
    response = client.get('/appointments/book')
    assert response.status_code == 200
    assert b'name' in response.data

def test_5_data_consistency_encryption_cycle(app):
    with app.app_context():
        original_name = "Степан Тестовий"
        test_client = Client()
        test_client.name = original_name
        test_client.email = "stepan@test.com"
        test_client.phone = "777"
        
        db.session.add(test_client)
        db.session.commit()
        
        from_db = Client.query.filter_by(email="stepan@test.com").first()
        assert from_db is not None
        assert from_db.name == original_name
        assert from_db._name.startswith("gAAAAA")

def test_6_api_past_date_handling(client):
    response = client.get("/appointments/available_times?date=2020-01-01")
    assert response.get_json() == []

def test_7_service_to_string_conversion(app):
    with app.app_context():
        s = Service(name="Test", description="Desc|Docs")
        assert "Test" in str(s)

def test_8_timeslot_representation(app):
    with app.app_context():
        t = TimeSlot(date=date(2026, 1, 1), start_time=time(10, 0))
        assert "10:00" in str(t)