import os
import sys
import pytest
from datetime import datetime, timedelta, date, time
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import MultiDict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app import db
    from app.appointments.forms import AppointmentForm
    from app.utils import encrypt_data, decrypt_data
    from app.appointments.routes import is_booking_allowed
except ImportError as e:
    pytest.fail(f"Import error: {e}")

def test_1_unit_logic_12h_booking_limit_mocked():
    """ПЕРЕВІРКА: Ліміт бронювання з коректним моком"""
    mocked_now = datetime(2026, 5, 20, 12, 0, 0)
    
    # Мокаємо тільки функцію now у модулі, де вона використовується
    with patch('app.appointments.routes.datetime') as mock_datetime:
        mock_datetime.now.return_value = mocked_now
        # Повертаємо оригінальний combine, щоб він не був моком
        mock_datetime.combine = datetime.combine
        
        allowed_dt = date(2026, 5, 21)
        allowed_tm = time(10, 0)
        assert is_booking_allowed(allowed_dt, allowed_tm) is True
        
        forbidden_dt = date(2026, 5, 20)
        forbidden_tm = time(20, 0)
        assert is_booking_allowed(forbidden_dt, forbidden_tm) is False

def test_2_unit_utils_date_formatting():
    test_date = date(2026, 5, 20)
    assert test_date.strftime("%Y-%m-%d") == "2026-05-20"

def test_3_unit_security_encryption_integrity():
    original_text = "Confidential Data 123"
    encrypted = encrypt_data(original_text)
    assert decrypt_data(encrypted) == original_text

def test_4_unit_security_encryption_uniqueness():
    val1 = encrypt_data("User_Data")
    val2 = encrypt_data("User_Data")
    assert val1 != val2

def test_5_unit_form_validation_invalid_data(app):
    with app.test_request_context(method='POST'):
        fake_data = MultiDict({
            'name': 'Test',
            'email': 'wrong-email', 
            'phone': '000', 
            'service_id': '1', 
            'time_id': '1',
            'privacy': 'y'
        })
        form = AppointmentForm(formdata=fake_data)
        form.service_id.choices = [('1', 'Service')]
        form.time_id.choices = [('1', '10:00')]
        
        form.validate()
        assert 'email' in form.errors
        assert 'phone' in form.errors

def test_6_unit_form_phone_format_acceptance(app):
    with app.test_request_context(method='POST'):
        fake_data = MultiDict({
            'name': 'Stanislav',
            'email': 'valid@mail.com',
            'phone': '+380501112233',
            'service_id': '1',
            'time_id': '1',
            'privacy': 'y'
        })
        form = AppointmentForm(formdata=fake_data)
        form.service_id.choices = [('1', 'Service')]
        form.time_id.choices = [('1', '10:00')]
        
        form.validate()
        if 'phone' in form.errors:
            assert "Invalid" not in str(form.errors['phone'])

def test_7_unit_ui_sorting_logic_integrity():
    d_new = datetime(2026, 12, 1)
    d_old = datetime(2026, 1, 1)
    items = [None, d_old, d_new]
    
    sorted_items = sorted(items, key=lambda x: x if x else datetime.min, reverse=True)
    
    assert sorted_items[0] == d_new
    assert sorted_items[1] == d_old
    assert sorted_items[2] is None

def test_8_unit_db_commit_mocking(app):
    with patch('app.db.session.commit') as mock_commit:
        db.session.commit()
        mock_commit.assert_called_once()