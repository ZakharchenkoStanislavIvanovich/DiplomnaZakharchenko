from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email
from app.models import Service

class AppointmentForm(FlaskForm):
    name = StringField("Ваше ім'я", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    service_id = SelectField("Послуга", coerce=int, validators=[DataRequired()])
    date = DateField("Дата", format='%Y-%m-%d', validators=[DataRequired()])
    time_id = SelectField("Час", coerce=int, choices=[], validators=[DataRequired()])
    submit = SubmitField("Записатися")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # список послуг
        self.service_id.choices = [
            (s.id, s.name) for s in Service.query.order_by(Service.name).all()
        ]
        # час підтягуємо AJAX-ом
        self.time_id.choices = []
