import pytest
import os
from sqlalchemy import create_engine
from app import create_app, db as _db_original

@pytest.fixture(scope='session')
def app():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "WTF_CSRF_ENABLED": False
    })
    
    with app.app_context():
        test_engine = create_engine('sqlite:///:memory:')
        
        _db_original.session.remove()
        _db_original.session.configure(bind=test_engine)
        
        _db_original.metadata.create_all(bind=test_engine)
        
        yield app
        test_engine.dispose()

@pytest.fixture
def client(app):
    """Фікстура для імітації HTTP-запитів"""
    return app.test_client()

@pytest.fixture
def db(app):
    """Фікстура для доступу до бази в тестах"""
    return _db_original

@pytest.fixture(autouse=True)
def _db_cleanup(app):
    """Очищення бази після кожного тесту (всередині SQLite RAM)"""
    with app.app_context():
        yield
        _db_original.session.rollback()