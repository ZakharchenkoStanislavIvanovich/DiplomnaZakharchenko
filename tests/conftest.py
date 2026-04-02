import pytest
import os
from app import create_app, db
from sqlalchemy import create_engine

@pytest.fixture(scope='session')
def app():
    # 1. Силова ізоляція оточення
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_ENGINE_OPTIONS": {} 
    })

    with app.app_context():
        # 2. Створюємо чистий тестовий двигун
        test_engine = create_engine('sqlite:///:memory:')
        
        # 3. Переприв'язуємо сесію
        db.session.remove()
        db.session.configure(bind=test_engine)
        
        # 4. Створюємо таблиці (використовуємо метадані напряму, це надійніше)
        db.metadata.create_all(bind=test_engine)
        
        yield app
        test_engine.dispose()

@pytest.fixture
def _db(app):
    with app.app_context():
        yield db
        db.session.rollback()