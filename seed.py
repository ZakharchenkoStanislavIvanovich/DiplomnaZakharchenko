from app import create_app, db
from app.models import Service, Client, Appointment, TimeSlot, User
from datetime import date, time, datetime, timedelta
from werkzeug.security import generate_password_hash

app = create_app()

def seed_data():
    with app.app_context():

        Appointment.query.delete()
        Client.query.delete()
        Service.query.delete()
        TimeSlot.query.delete()
        User.query.delete() 
        db.session.commit()

        admin = User(
            username='admin',
            email='admin@notary.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)

        services = [
            Service(name="Оформлення довіреності", description="Складання та посвідчення довіреностей"),
            Service(name="Посвідчення копій документів", description="Офіційне засвідчення копій документів"),
            Service(name="Оформлення заповіту", description="Складання та посвідчення заповіту"),
        ]
        db.session.add_all(services)

        today = date.today()
        tomorrow = today + timedelta(days=1)

        schedule = [
            TimeSlot(date=today, start_time=time(10, 0), is_booked=False),
            TimeSlot(date=today, start_time=time(11, 0), is_booked=False),
            TimeSlot(date=tomorrow, start_time=time(12, 0), is_booked=False),
            TimeSlot(date=tomorrow, start_time=time(14, 30), is_booked=False),
        ]
        db.session.add_all(schedule)

        db.session.commit()
        print("✅ Postgres успішно наповнено: створено адміна, послуги та розклад!")

if __name__ == '__main__':
    seed_data()