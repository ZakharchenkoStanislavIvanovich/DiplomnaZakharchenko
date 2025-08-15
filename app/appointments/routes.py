from app.appointments import bp
from flask import render_template, redirect, url_for, flash, request, jsonify
from app import db
from app.models import Client, Appointment, NotarySchedule, Service
from .forms import AppointmentForm
from datetime import date, datetime


@bp.route('/available_times')
def available_times():
    """AJAX — повертає вільні години для обраної дати."""
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify([])

    schedules = NotarySchedule.query.filter_by(
        schedule_date=date_obj,
        is_available=True
    ).all()

    times = [s.schedule_time.strftime("%H:%M") for s in schedules]
    return jsonify(times)


@bp.route('/book', methods=['GET', 'POST'])
def book():
    """Запис клієнта через публічну форму."""
    form = AppointmentForm()
    form.service_id.choices = [(s.id, s.name) for s in Service.query.all()]

    if form.validate_on_submit():
        # Додаємо або отримуємо клієнта
        client = Client.query.filter_by(email=form.email.data).first()
        if not client:
            client = Client(name=form.name.data, email=form.email.data)
            db.session.add(client)
            db.session.commit()

        # Отримуємо обраний слот
        slot = NotarySchedule.query.get(form.schedule_id.data)

        if slot and slot.is_available and slot.schedule_date >= date.today():
            exists = Appointment.query.filter_by(
                client_id=client.id,
                appointment_date=slot.schedule_date,
                appointment_time=slot.schedule_time
            ).first()
            if exists:
                flash("❌ Ви вже записані на цей час.", "warning")
                return redirect(url_for('appointments.book'))

            appointment = Appointment(
                client_id=client.id,
                service_id=form.service_id.data,
                appointment_date=slot.schedule_date,
                appointment_time=slot.schedule_time,
                status='очікує'
            )
            db.session.add(appointment)
            slot.is_available = False
            db.session.commit()

            flash("✅ Ви успішно записані на прийом!", "success")
            return redirect(url_for('main.index'))
        else:
            flash("❌ Обраний час недоступний або вже минув", "danger")

    return render_template('appointments/book.html', form=form)