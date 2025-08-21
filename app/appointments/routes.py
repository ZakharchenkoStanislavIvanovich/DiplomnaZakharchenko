from flask import render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.appointments import bp
from app.appointments.forms import AppointmentForm
from app.models import Appointment, TimeSlot, Client
from datetime import datetime

@bp.route("/book", methods=["GET", "POST"])
def book():
    form = AppointmentForm()

    # --- Підвантажити доступні слоти для обраної дати перед validate_on_submit
    if request.method == "POST" and form.date.data:
        slots = TimeSlot.query.filter_by(date=form.date.data, is_booked=False).order_by(TimeSlot.start_time).all()
        form.time_id.choices = [(s.id, s.start_time.strftime("%H:%M")) for s in slots]


    if form.validate_on_submit():
        # знайти або створити клієнта
        client = Client.query.filter_by(email=form.email.data).first()
        if not client:
            client = Client(name=form.name.data, email=form.email.data)
            db.session.add(client)
            db.session.flush()  # отримати client.id без окремого commit

        # вибраний слот
        slot = TimeSlot.query.get(form.time_id.data)
        if not slot or slot.is_booked:
            flash("❌ Обраний час недоступний або вже заброньований.", "danger")
            return redirect(url_for("appointments.book"))

        # створення заявки
        appointment = Appointment(
            client_id=client.id,
            service_id=form.service_id.data,
            slot_id=slot.id,
            status="очікує"
        )
        db.session.add(appointment)

        # позначити слот зайнятим
        slot.is_booked = True
        db.session.commit()

        flash("✅ Ви успішно записані на прийом!", "success")
        return redirect(url_for("appointments.book"))

    if request.method == "POST":
        # форма не пройшла валідацію
        flash("❌ Форма невалідна. Перевірте введені дані.", "danger")
        # для відладки у консоль
        print("DEBUG form errors:", form.errors)

    return render_template("appointments/book.html", form=form)

@bp.route("/available_times")
def available_times():
    """
    Повертає JSON: список вільних слотів для обраної дати.
    Вхід: ?date=YYYY-MM-DD
    """
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        return jsonify([])

    slots = (
        TimeSlot.query
        .filter_by(date=selected_date, is_booked=False)
        .order_by(TimeSlot.start_time)
        .all()
    )

    return jsonify([
        {"id": s.id, "display": s.start_time.strftime("%H:%M")}
        for s in slots
    ])
