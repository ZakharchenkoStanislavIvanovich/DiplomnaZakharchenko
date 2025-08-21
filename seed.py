from app import create_app, db
from app.models import Service, Client, Appointment, TimeSlot
from datetime import date, time

app = create_app()

with app.app_context():
    # Очистимо таблиці (щоб не плодились дублікати при повторному запуску)
    Appointment.query.delete()
    Client.query.delete()
    Service.query.delete()
    TimeSlot.query.delete()
    db.session.commit()

    # --- Послуги ---
    services = [
        Service(name="Оформлення довіреності", description="Складання та посвідчення довіреностей"),
        Service(name="Посвідчення копій документів", description="Офіційне засвідчення копій документів"),
        Service(name="Оформлення заповіту", description="Складання та посвідчення заповіту"),
    ]
    db.session.add_all(services)
    db.session.commit()

    # --- Слоти нотаріуса ---
    schedule = [
        TimeSlot(date=date(2025, 8, 21), start_time=time(10, 0), is_booked=False),
        TimeSlot(date=date(2025, 8, 21), start_time=time(11, 0), is_booked=False),
        TimeSlot(date=date(2025, 8, 21), start_time=time(12, 0), is_booked=False),
        TimeSlot(date=date(2025, 8, 22), start_time=time(9, 30), is_booked=False),
    ]
    db.session.add_all(schedule)
    db.session.commit()

    print("✅ Тестові дані успішно додані!")
