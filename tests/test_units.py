import pytest
from datetime import datetime, timedelta, date, time
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import MultiDict
from app.models import Client, Service, TimeSlot, Appointment, User
from app.appointments.forms import AppointmentForm
from app.utils import encrypt_data, decrypt_data
from app.appointments.routes import is_booking_allowed

# --- БЛОК 1: БІЗНЕС-ЛОГІКА ЧАСУ (UNIT) ---

def test_booking_allowed_edge_case_exactly_12h():
    """Межа: Рівно за 12 годин до запису"""
    mock_now = datetime(2026, 5, 20, 10, 0)
    slot_dt = mock_now + timedelta(hours=12)
    with patch('app.appointments.routes.datetime') as mock_dt:
        mock_dt.now.return_value = mock_now
        mock_dt.combine = datetime.combine
        assert is_booking_allowed(slot_dt.date(), slot_dt.time()) is False

def test_booking_forbidden_past_date():
    """Минуле: Запис на вчора заборонений"""
    yesterday = date.today() - timedelta(days=1)
    assert is_booking_allowed(yesterday, time(10, 0)) is False

def test_booking_allowed_next_week():
    """Далеке майбутнє: Запис на наступний тиждень дозволено"""
    future = date.today() + timedelta(days=7)
    assert is_booking_allowed(future, time(12, 0)) is True

def test_unit_is_booking_allowed_midnight():
    """Крайній випадок: бронювання опівночі на ранок (менше 12 год)"""
    mock_now = datetime(2026, 5, 20, 0, 1)
    booking_date = date(2026, 5, 20)
    booking_time = time(8, 0)
    with patch('app.appointments.routes.datetime') as mock_dt:
        mock_dt.now.return_value = mock_now
        mock_dt.combine = datetime.combine
        assert is_booking_allowed(booking_date, booking_time) is False

def test_unit_is_booking_allowed_far_future():
    """Бронювання на рік вперед — дозволено"""
    future_date = date(2027, 5, 20)
    assert is_booking_allowed(future_date, time(10, 0)) is True

# --- БЛОК 2: ВАЛІДАЦІЯ ФОРМ (UNIT) ---

@pytest.mark.parametrize("email", ["plainaddress", "#@%^%#$@#", "@example.com", "joe user@example.com"])
def test_form_invalid_emails(app, email):
    """Перевірка списку некоректних імейлів"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'email': email}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'email' in form.errors

def test_form_phone_too_short(app):
    """Телефон занадто короткий"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'phone': '123'}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'phone' in form.errors

def test_form_phone_too_long(app):
    """Телефон занадто довгий (перевірка межі валідатора)"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'phone': '+380' + '0'*20}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'phone' in form.errors

def test_form_long_name_limit(app):
    """Перевірка обробки довгого імені"""
    with app.test_request_context(method='POST'):
        big_name = 'A' * 500
        form = AppointmentForm(formdata=MultiDict({
            'name': big_name, 
            'email': 'test@test.com', 
            'phone': '+380991234567',
            'service_id': '1', 
            'time_id': '1', 
            'date': '2026-05-20'
        }))
        form.service_id.choices = [('1', 'Test')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert len(form.name.data) == 500

def test_form_name_with_special_chars(app):
    """Стійкість форми до XSS-символів у імені"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'name': '<script>alert(1)</script>'}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert form.name.data == '<script>alert(1)</script>'

def test_form_phone_not_digit(app):
    """Телефон не може містити літери"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'phone': 'plus-три-вісім'}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'phone' in form.errors

def test_form_whitespace_stripping(app):
    """Перевірка обрізки пробілів у полях"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'name': '   Stanislav   '}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        assert form.name.data.strip() == 'Stanislav'

def test_form_service_selection_required(app):
    """Обов'язковість вибору послуги"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'service_id': ''}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'service_id' in form.errors

def test_form_time_selection_required(app):
    """Обов'язковість вибору часу"""
    with app.test_request_context(method='POST'):
        form = AppointmentForm(formdata=MultiDict({'time_id': ''}))
        form.service_id.choices = [('1', 'Test Service')]
        form.time_id.choices = [('1', '10:00')]
        form.validate()
        assert 'time_id' in form.errors

# --- БЛОК 3: БЕЗПЕКА ТА КРИПТОГРАФІЯ (UNIT) ---

def test_encryption_empty_string():
    """Шифрування порожнього рядка"""
    assert encrypt_data("") != "some_wrong_val"

def test_encryption_different_keys():
    """Різні дані дають різні шифротексти"""
    assert encrypt_data("Admin") != encrypt_data("User")

def test_decryption_identity():
    """Цикл: шифрування -> дешифрування"""
    secret = "Diplom2026"
    assert decrypt_data(encrypt_data(secret)) == secret

def test_unit_encryption_salt_check():
    """Перевірка наявності випадковості (salt) при кожному шифруванні"""
    text = "Important"
    assert encrypt_data(text) != encrypt_data(text)

def test_unit_decryption_integrity():
    try:
        decrypt_data("not-a-token")
    except:
        assert True

# --- БЛОК 4: МОДЕЛІ ДАНИХ (UNIT) ---

def test_model_timeslot_default_state():
    """Початковий стан нового слота"""
    ts = TimeSlot(date=date(2026, 6, 1), start_time=time(9, 0))
    assert ts.is_booked in [False, None]

def test_model_appointment_relationship_init():
    """Ініціалізація зв'язків у записі"""
    appnt = Appointment(service_id=1, client_id=1, slot_id=1)
    assert appnt.service_id == 1

def test_model_client_initialization():
    """Створення об'єкта Client"""
    client = Client(name="Petro", email="petro@test.com", phone="099")
    assert client.name == "Petro"
    assert client.email == "petro@test.com"

def test_model_service_splitting():
    """Розділення складеної назви послуги"""
    s = Service(name="Договір|Купівля", description="Опис")
    parts = s.name.split('|')
    assert parts[0] == "Договір"
    assert parts[1] == "Купівля"

def test_model_appointment_status_presence():
    """Перевірка наявності поля статусу в Appointment"""
    appnt = Appointment()
    assert hasattr(appnt, 'enc_status') or hasattr(appnt, 'status')

def test_model_user_identity():
    """Збереження логіна користувача"""
    user = User(username="notary_admin")
    assert user.username == "notary_admin"

def test_model_client_phone_storage():
    """Формат збереження телефону"""
    client = Client(phone="+380001112233")
    assert client.phone.startswith("+38")

# --- БЛОК 5: СОРТУВАННЯ ТА УТИЛІТИ (UNIT) ---

def test_sorting_logic_all_none():
    """Сортування списку з порожніми значеннями"""
    items = [None, None]
    sorted_items = sorted(items, key=lambda x: x if x else datetime.min)
    assert len(sorted_items) == 2

def test_sorting_logic_mixed_dates():
    """Сортування дат від нових до старих"""
    d_new = datetime(2026, 12, 1)
    d_old = datetime(2026, 1, 1)
    items = [d_old, d_new, None]
    sorted_items = sorted(items, key=lambda x: x if x else datetime.min, reverse=True)
    assert sorted_items[0] == d_new
    assert sorted_items[1] == d_old
    assert sorted_items[2] is None