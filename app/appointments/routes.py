from flask import render_template, request, redirect, url_for, flash, jsonify
from app import db, mail
from app.appointments import bp
from app.appointments.forms import AppointmentForm
from app.models import Appointment, TimeSlot, Client
from datetime import datetime, timedelta
from flask_mail import Message
from app.utils import encrypt_data


def is_booking_allowed(slot_date, slot_time):
    """
    Бізнес-логіка: перевіряє, чи доступне бронювання.
    Запис можливий щонайменше за 12 годин до початку.
    """
    slot_dt = datetime.combine(slot_date, slot_time)
    return slot_dt > datetime.now() + timedelta(hours=12)

@bp.route("/book", methods=["GET", "POST"])
def book():
    form = AppointmentForm()

    if request.method == "POST" and form.date.data:
        all_slots = TimeSlot.query.filter_by(date=form.date.data, is_booked=False).order_by(TimeSlot.start_time).all()
        form.time_id.choices = [(s.id, s.start_time.strftime("%H:%M")) for s in all_slots if is_booking_allowed(s.date, s.start_time)]

    if form.validate_on_submit():
        try:
            slot_id = int(form.time_id.data)
            slot = db.session.query(TimeSlot).filter_by(id=slot_id, is_booked=False).with_for_update().first()
            
            if not slot:
                db.session.rollback()
                flash("Цей час уже заброньовано.", "danger")
                return redirect(url_for("appointments.book"))

            client = Client()
            client.name = form.name.data
            client.email = form.email.data
            client.phone = form.phone.data
            db.session.add(client)
            db.session.flush()

            new_appointment = Appointment()
            new_appointment.client_id = client.id
            new_appointment.service_id = form.service_id.data
            new_appointment.slot_id = slot.id
            new_appointment.status = "очікує"
            db.session.add(new_appointment)

            slot.is_booked = True
            
            db.session.commit()

            try:
                msg = Message("Запис підтверджено", recipients=[form.email.data])
                msg.html = render_template('email/received.html', 
                                         client=client, 
                                         appointment=new_appointment) 
                mail.send(msg)
            except Exception as mail_err:
                print(f"Mail error: {mail_err}")

            return redirect(url_for("appointments.success"))

        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
            flash("Помилка при бронюванні. Спробуйте ще раз.", "danger")
            return redirect(url_for("appointments.book"))

    return render_template("appointments/book.html", form=form)

@bp.route("/available_times")
def available_times():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify([])

    slots = TimeSlot.query.filter_by(date=selected_date, is_booked=False).order_by(TimeSlot.start_time).all()
    
    return jsonify([{
        "id": s.id, 
        "display": s.start_time.strftime("%H:%M")
    } for s in slots if is_booking_allowed(s.date, s.start_time)])

@bp.route("/success")
def success():
    return render_template("appointments/success.html")