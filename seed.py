from app import create_app, db
from app.models import Service, Client, Appointment, TimeSlot
from datetime import date, time

app = create_app()

with app.app_context():
    Appointment.query.delete()
    Client.query.delete()
    Service.query.delete()
    TimeSlot.query.delete()
    db.session.commit()

    services = [
        Service(name="Оформлення довіреності", description="Складання та посвідчення довіреностей"),
        Service(name="Посвідчення копій документів", description="Офіційне засвідчення копій документів"),
        Service(name="Оформлення заповіту", description="Складання та посвідчення заповіту"),
    ]
    db.session.add_all(services)
    db.session.commit()

    schedule = [
        TimeSlot(date=date(2026, 2, 9), start_time=time(10, 0), is_booked=False),
        TimeSlot(date=date(2026, 2, 9), start_time=time(11, 0), is_booked=False),
        TimeSlot(date=date(2026, 2, 10), start_time=time(12, 0), is_booked=False),
        TimeSlot(date=date(2026, 2, 10), start_time=time(14, 30), is_booked=False),
    ]
    db.session.add_all(schedule)
    db.session.commit()

    print("✅ Тестові дані успішно додані!")
