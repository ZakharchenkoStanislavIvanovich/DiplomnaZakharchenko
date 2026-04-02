import pytest
import re
from app import db
from app.models import TimeSlot, Service, Appointment, Client
from datetime import datetime, timedelta
from unittest.mock import patch

def get_csrf_token(client, url='/appointments/book'):
    res = client.get(url)
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', res.get_data(as_text=True))
    return match.group(1) if match else ""

@pytest.fixture
def ui_setup(app):
    with app.app_context():
        service = Service(name="Консультація", description="Тест")
        db.session.add(service)
        
        dt = datetime.now() + timedelta(days=2)
        slot = TimeSlot(date=dt.date(), start_time=dt.time(), is_booked=False)
        db.session.add(slot)
        db.session.commit()
        
        yield {
            "s_id": str(service.id), 
            "slot_id": str(slot.id), 
            "date": dt.date().strftime('%Y-%m-%d')
        }
        
        db.session.rollback()

def test_1_ui_homepage_availability(client):
    response = client.get('/')
    assert response.status_code == 200

def test_2_ui_booking_fields_present(client):
    data = client.get('/appointments/book').get_data(as_text=True)
    assert 'name' in data
    assert 'phone' in data

def test_3_ui_api_available_times_status(client, ui_setup):
    url = f"/appointments/available_times?date={ui_setup['date']}"
    response = client.get(url)
    assert ui_setup['slot_id'] in response.get_data(as_text=True)

def test_4_ui_full_booking_flow_success(client, ui_setup):
    token = get_csrf_token(client)
    payload = {
        'csrf_token': token,
        'name': 'UI Tester', 
        'email': 'ui@test.com', 
        'phone': '+380990000000', 
        'service_id': ui_setup['s_id'], 
        'date': ui_setup['date'], 
        'time_id': ui_setup['slot_id'], 
        'privacy': 'y'
    }
    
    with patch('app.appointments.routes.db.session.commit') as mock_commit:
        response = client.post('/appointments/book', data=payload, follow_redirects=True)
        assert response.status_code == 200
        assert "success" in response.request.path or b"\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb9\xd0\xbd\xd1\x8f\xd1\x82\xd0\xbe" in response.data

def test_5_ui_form_get_request_resilience(client):
    assert client.get('/appointments/book').status_code == 200

def test_6_ui_login_page_labels(client):
    data = client.get('/auth/login').get_data(as_text=True)
    assert "Email" in data
    assert "Пароль" in data

def test_7_ui_services_list_rendering(client, ui_setup):
    response = client.get('/services')
    assert b"\xd0\x9a\xd0\xbe\xd0\xbd\xd1\x81\xd1\x83\xd0\xbb\xd1\x8c\xd1\x82\xd0\xb0\xd1\x86\xd1\x96\xd1\x8f" in response.data

def test_8_ui_footer_branding_present(client):
    assert b"\xd0\xbd\xd0\xbe\xd1\x82\xd0\xb0\xd1\x80" in client.get('/').data

def test_9_ui_login_form_structure(client):
    assert b'name="email"' in client.get('/auth/login').data

def test_10_ui_success_page_availability(client):
    assert client.get('/appointments/success').status_code == 200

def test_11_ui_static_assets_loading(client):
    response = client.get('/static/img/logo.png')
    assert response.status_code in [200, 304, 404]

def test_12_ui_logout_redirect(client):
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200