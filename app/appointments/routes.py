from flask import render_template, request, redirect, url_for, flash, jsonify
from app import db, mail
from app.appointments import bp
from app.appointments.forms import AppointmentForm
from app.models import Appointment, TimeSlot, Client
from datetime import datetime
from flask_mail import Message

@bp.route("/book", methods=["GET", "POST"])
def book():
    form = AppointmentForm()

    if request.method == "POST" and form.date.data:
        slots = TimeSlot.query.filter_by(date=form.date.data, is_booked=False).order_by(TimeSlot.start_time).all()
        form.time_id.choices = [(s.id, s.start_time.strftime("%H:%M")) for s in slots]

    if form.validate_on_submit():
        client = Client.query.filter_by(email=form.email.data).first()
        if not client:
            client = Client(name=form.name.data, email=form.email.data)
            db.session.add(client)
            db.session.flush()

        slot = TimeSlot.query.get(form.time_id.data)
        if not slot or slot.is_booked:
            flash("Обраний час недоступний або вже заброньований.", "danger")
            return redirect(url_for("appointments.book"))

        appointment = Appointment(
            client_id=client.id,
            service_id=form.service_id.data,
            slot_id=slot.id,
            status="очікує"
        )
        db.session.add(appointment)

        slot.is_booked = True
        db.session.commit()

        try:
            msg = Message("Ваша заявка до нотаріуса отримана",
                          recipients=[client.email])
            msg.html = render_template('email/received.html', client=client, appointment=appointment)
            mail.send(msg)
        except Exception as e:
            print(f"DEBUG: Помилка відправки пошти: {e}")

        return redirect(url_for("appointments.success"))

    if request.method == "POST" and not form.validate_on_submit():
        flash("Перевірте введені дані.", "danger")
        print("DEBUG form errors:", form.errors)

    return render_template("appointments/book.html", form=form)

@bp.route("/available_times")
def available_times():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return jsonify([])

    slots = TimeSlot.query.filter_by(date=selected_date, is_booked=False).order_by(TimeSlot.start_time).all()
    return jsonify([{"id": s.id, "display": s.start_time.strftime("%H:%M")} for s in slots])

@bp.route("/success")
def success():
    return render_template("appointments/success.html")