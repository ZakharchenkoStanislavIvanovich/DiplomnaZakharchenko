import pytest
from app import db
from app.models import Client, Service, TimeSlot
from app.utils import encrypt_data, decrypt_data
from sqlalchemy import text
from datetime import datetime
from unittest.mock import patch

@pytest.fixture
def security_setup(app):
    with app.app_context():
        s = Service(name="Security Service", description="Secret|Data")
        t = TimeSlot(date=datetime.now().date(), start_time=datetime.now().time(), is_booked=False)
        db.session.add_all([s, t])
        db.session.commit()
        
        yield {"s_id": str(s.id), "t_id": str(t.id)}
        db.session.rollback()

def test_1_security_at_rest_encryption(app, security_setup):
    with app.app_context():
        raw_name = "Конфіденційне Ім'я"
        client = Client()
        client.name = raw_name
        client.email = "admin@notary.com"
        client.phone = "000"
        db.session.add(client)
        db.session.commit()
        
        res = db.session.execute(text("SELECT enc_name FROM client WHERE email = 'admin@notary.com'")).fetchone()
        
        assert res is not None
        encrypted_value = res[0]
        
        assert raw_name not in encrypted_value
        assert encrypted_value.startswith("gAAAAA")

def test_2_security_decryption_accuracy():
    original = "Secret123"
    assert decrypt_data(encrypt_data(original)) == original

def test_3_security_unique_tokens():
    data = "SameData"
    assert encrypt_data(data) != encrypt_data(data)

def test_4_security_sql_injection_resilience(client, security_setup):
    payload = {
        'name': "'; DROP TABLE client; --",
        'email': 'hacker@test.com',
        'phone': '+380991234567',
        'service_id': security_setup['s_id'],
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time_id': security_setup['t_id'],
        'privacy': 'y'
    }
    
    with patch('app.appointments.routes.db.session.commit') as mock_commit:
        response = client.post('/appointments/book', data=payload)
        assert response.status_code < 500

def test_5_security_encryption_layer_count():
    data = "TripleCheck"
    encrypted = encrypt_data(data)
    # Перевірка, що шифрування не 'злетіло' до відкритого тексту
    with pytest.raises(Exception):
        decrypt_data(data)
    assert decrypt_data(encrypted) == data

def test_6_security_unauthorized_admin_access(client):
    response = client.get('/admin/dashboard', follow_redirects=True)
    # Має перенаправити на логін
    assert b"/auth/login" in response.data or b"login" in response.request.path.lower()

def test_7_security_csrf_protection_presence(client, app):
    app.config['WTF_CSRF_ENABLED'] = True
    response = client.get('/auth/login')
    assert b'name="csrf_token"' in response.data
    app.config['WTF_CSRF_ENABLED'] = False

def test_8_security_headers_check(client):
    response = client.get('/')
    # Перевірка базових заголовків безпеки, якщо вони налаштовані
    if 'X-Content-Type-Options' in response.headers:
        assert response.headers['X-Content-Type-Options'] == 'nosniff'

def test_9_security_password_hashing_logic():
    from werkzeug.security import generate_password_hash, check_password_hash
    pw = "StrongPass123!"
    hash_val = generate_password_hash(pw)
    assert pw != hash_val
    assert check_password_hash(hash_val, pw) is True

def test_10_security_data_leakage_in_error(client):
    response = client.get('/appointments/available_times?date=invalid-date')
    data = response.get_data(as_text=True)
    assert "/usr/local/app" not in data
    assert "Traceback" not in data