from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email
from app.models import Service, NotarySchedule
from datetime import date

class AppointmentForm(FlaskForm):
    name = StringField("Ім’я", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    service_id = SelectField("Послуга", coerce=int, validators=[DataRequired()])
    schedule_id = SelectField("Час прийому", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Записатись")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Підтягуємо всі послуги
        self.service_id.choices = [
            (s.id, s.name) for s in Service.query.order_by(Service.name).all()
        ]
        # Тільки вільний час і тільки майбутні дати
        self.schedule_id.choices = [
            (
                n.id,
                f"{n.schedule_date.strftime('%d.%m.%Y')} | {n.schedule_time.strftime('%H:%M')}"
            )
            for n in NotarySchedule.query
                .filter_by(is_available=True)
                .filter(NotarySchedule.schedule_date >= date.today())
                .order_by(NotarySchedule.schedule_date, NotarySchedule.schedule_time)
                .all()
        ]