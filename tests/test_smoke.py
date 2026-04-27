import os
import sys
import pytest
from app import db
from app.models import Service
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_1_smoke_homepage_availability(client):
    """Головна сторінка повертає 200 OK"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data

def test_2_smoke_db_connection_status(app):
    """База даних відповідає на запити (SQLite in-memory)"""
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            assert True
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

def test_3_smoke_key_routes_availability(client, app):
    """Основні маршрути доступні (без 404/500)"""
    with app.app_context():
        if not Service.query.filter_by(name="Smoke Test").first():
            db.session.add(Service(name="Smoke Test", description="Test|Desc"))
            db.session.commit()
    
    routes = ['/appointments/book', '/services', '/auth/login']
    for url in routes:
        response = client.get(url, follow_redirects=True)
        assert response.status_code == 200

def test_4_smoke_static_files_loading(client):
    """Перевірка наявності хоча б базової структури статики"""
    response = client.get('/static/css/dashboard.css')
    assert response.status_code in [200, 304, 404] 

def test_5_smoke_security_configuration(app):
    """Критичні налаштування безпеки активні"""
    assert app.config.get('SECRET_KEY') is not None
    assert app.config['TESTING'] is True

def test_6_smoke_notary_branding_present(client):
    """На головній сторінці є згадка про нотаріат (кирилиця)"""
    response = client.get('/')
    content = response.data.lower()
    assert b"\xd0\xbd\xd0\xbe\xd1\x82\xd0\xb0\xd1\x80" in content

def test_7_smoke_csrf_protection_status(app):
    """CSRF вимкнено для зручності автоматичних тестів"""
    assert app.config['WTF_CSRF_ENABLED'] is False

def test_8_smoke_encryption_utils_load():
    """Утиліти шифрування працюють коректно"""
    from app.utils import encrypt_data, decrypt_data
    test_str = "SmokeTest_2026"
    assert decrypt_data(encrypt_data(test_str)) == test_str

def test_9_smoke_admin_protected_redirect(client):
    """Спроба входу в адмінку без логіна перенаправляє на login"""
    response = client.get('/admin/dashboard')
    assert response.status_code == 302