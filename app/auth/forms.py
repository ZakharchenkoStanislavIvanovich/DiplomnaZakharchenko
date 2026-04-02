from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()]) # Тимчасово прибрали Email()
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Увійти')