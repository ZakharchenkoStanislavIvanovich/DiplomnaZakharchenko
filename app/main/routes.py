from app.main import bp
from flask import render_template, redirect, url_for, flash
from app.main.forms import RegistrationForm
from app import db
from app.models import Client

@bp.route('/')
def index():
    return render_template('main/index.html')

@bp.route('/contacts')
def contacts():
    return render_template('main/contacts.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Перевірка, чи email вже є в базі
        existing_client = Client.query.filter_by(email=form.email.data).first()
        if existing_client:
            flash('Клієнт з таким email вже зареєстрований.', 'warning')
            return redirect(url_for('main.register'))

        new_client = Client(name=form.name.data, email=form.email.data)
        db.session.add(new_client)
        db.session.commit()
        flash('Реєстрація успішна!', 'success')
        return redirect(url_for('main.index'))
    return render_template('main/register.html', form=form)