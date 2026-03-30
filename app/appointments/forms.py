from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Regexp
from app.models import Service
from flask import request

class AppointmentForm(FlaskForm):
    name = StringField("Ваше ім'я", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    
    phone = StringField("Номер телефону", validators=[
        DataRequired(),
        Regexp(r'^\+?380\d{9}$', message="Формат: +380XXXXXXXXX")
    ])
    
    service_id = SelectField("Послуга", coerce=int, validators=[DataRequired()])
    date = DateField("Дата", format='%Y-%m-%d', validators=[DataRequired()])
    time_id = SelectField("Час", validators=[DataRequired()])
    submit = SubmitField("Записатися")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        all_services = Service.query.all()
        all_services.sort(key=lambda x: x.name)
        self.service_id.choices = [(s.id, s.name) for s in all_services]

        if request.method == 'POST':
            s_id = request.form.get('service_id')
            t_id = request.form.get('time_id')
            if s_id:
                self.service_id.choices = [(s_id, '')]
            if t_id:
                self.time_id.choices = [(t_id, '')]
        else:
            self.time_id.choices = []