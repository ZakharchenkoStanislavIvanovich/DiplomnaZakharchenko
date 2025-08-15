from app import create_app, db
from app.models import Service, NotarySchedule
from datetime import date, time

app = create_app()

with app.app_context():
    # Додати послуги, якщо вони ще не існують
    if Service.query.count() == 0:
        services = [
            Service(name="Оформлення довіреності", description="Складання та посвідчення довіреностей"),
            Service(name="Посвідчення копій документів", description="Офіційне засвідчення копій документів"),
            Service(name="Оформлення заповіту", description="Складання та посвідчення заповіту")
        ]
        db.session.add_all(services)

    # Додати доступний розклад нотаріуса, якщо ще немає
    if NotarySchedule.query.count() == 0:
        schedule = [
            NotarySchedule(schedule_date=date(2025, 8, 15), schedule_time=time(10, 0), is_available=True),
            NotarySchedule(schedule_date=date(2025, 8, 15), schedule_time=time(11, 0), is_available=True),
            NotarySchedule(schedule_date=date(2025, 8, 15), schedule_time=time(12, 0), is_available=False),  # зайнятий час
            NotarySchedule(schedule_date=date(2025, 8, 16), schedule_time=time(9, 30), is_available=True)
        ]
        db.session.add_all(schedule)

    db.session.commit()
    print("✅ Тестові дані успішно додані!")