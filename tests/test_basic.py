import pytest
from app import create_app, db
from sqlalchemy import text

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_homepage(client):
    """Перевірка, чи головна сторінка відкривається успішно"""
    response = client.get('/')
    assert response.status_code == 200

def test_db_connection(app):
    """Перевірка підключення до PostgreSQL"""
    with app.app_context():
        try:
            db.session.execute(text('SELECT 1'))
            assert True
        except Exception as e:
            pytest.fail(f"База даних недоступна: {e}")