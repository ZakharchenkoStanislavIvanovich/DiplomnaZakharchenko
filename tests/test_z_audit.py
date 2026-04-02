import pytest
from app import db
from app.models import Client, Appointment, Service, TimeSlot
from unittest.mock import patch

def test_1_database_cleanup_audit(app, _db):
    """
    ФІНАЛЬНИЙ АУДИТ: Перевірка ізоляції тестів.
    Гарантує, що кожен тест працює у власній стерильній транзакції в SQLite RAM.
    """
    with app.app_context():
        # Примусово очищуємо кеш сесії, щоб бачити реальний стан пам'яті
        db.session.expire_all()
        
        clients_count = Client.query.count()
        appointments_count = Appointment.query.count()
        
        error_msg = f"Порушено ізоляцію! Знайдено: {clients_count} клієнтів, {appointments_count} записів."
        
        # Оскільки ми в :memory: і conftest робить rollback/cleanup, тут має бути 0
        assert clients_count == 0, error_msg
        assert appointments_count == 0, error_msg

def test_2_database_rollback_mechanism(app, _db):
    """
    ПЕРЕВІРКА РОЛБЕКУ: Чи працює механізм відкату транзакцій.
    """
    with app.app_context():
        # Фіксуємо початковий стан
        count_before = Appointment.query.count()
        
        try:
            # Імітуємо додавання запису (без реальних Foreign Keys для швидкості)
            a = Appointment(slot_id=999, service_id=999, client_id=999)
            db.session.add(a)
            db.session.flush() # Відправляємо в базу, але не комітимо
            
            # Штучна помилка
            raise RuntimeError("Simulated transaction failure")
        except RuntimeError:
            db.session.rollback()
            
        count_after = Appointment.query.count()
        assert count_before == count_after, "Механізм rollback не спрацював у тестовому оточенні!"

def test_3_database_session_identity(app, _db):
    """
    ПЕРЕВІРКА СЕСІЇ: Перевірка, що об'єкти не дублюються в пам'яті.
    """
    with app.app_context():
        s1 = Service(name="Audit Service", description="Test|Docs")
        db.session.add(s1)
        db.session.commit()
        
        # Отримуємо той самий об'єкт двома способами
        s_by_query = Service.query.filter_by(name="Audit Service").first()
        s_by_get = db.session.get(Service, s1.id)
        
        assert s_by_query is s_by_get, "Identity Map зламана: різні об'єкти для одного ID"

def test_4_no_persistence_after_test(app):
    """
    ПЕРЕВІРКА ПАМ'ЯТІ: Дані не повинні жити довше одного контексту.
    """
    with app.app_context():
        # Цей тест просто перевіряє, що база пуста на момент старту
        # (підтвердження роботи SQLite :memory:)
        assert Client.query.count() == 0
        assert Service.query.count() == 0

def test_5_mock_safety_check():
    """
    АУДИТ МОКІВ: Перевірка, що MagicMock працює коректно.
    """
    mock_db = patch('app.db.session.commit')
    with mock_db as mocked:
        db.session.commit()
        assert mocked.called is True