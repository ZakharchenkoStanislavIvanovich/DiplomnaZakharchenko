from datetime import datetime, timedelta
from flask import render_template, abort, request, jsonify, make_response, current_app
from flask_login import login_required, current_user
from app.admin import bp
from app.models import Appointment, ArchivedAppointment, TimeSlot
from app import db, mail
from functools import wraps
from flask_mail import Message

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def cleanup_tasks():
    now = datetime.utcnow()
    three_days_ago = now - timedelta(days=3)
    to_archive = Appointment.query.filter(
        Appointment.status == 'відхилено',
        Appointment.updated_at <= three_days_ago
    ).all()
    
    for app in to_archive:
        archive_entry = ArchivedAppointment(
            original_id=app.id,
            client_name=app.client.name,
            client_email=app.client.email,
            service_name=app.service.name,
            slot_info=f"{app.slot.date.strftime('%d.%m.%Y')} {app.slot.start_time.strftime('%H:%M')}",
            status=app.status,
            deletion_type='automatic'
        )
        if app.slot:
            app.slot.is_booked = False
        db.session.add(archive_entry)
        db.session.delete(app)
    
    month_ago = now - timedelta(days=30)
    ArchivedAppointment.query.filter(ArchivedAppointment.deleted_at < month_ago).delete()
    db.session.commit()

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cleanup_tasks()
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template('admin/dashboard.html', appointments=appointments)

@bp.route('/archive')
@login_required
@admin_required
def archive():
    manual = ArchivedAppointment.query.filter_by(deletion_type='manual').order_by(ArchivedAppointment.deleted_at.desc()).all()
    auto = ArchivedAppointment.query.filter_by(deletion_type='automatic').order_by(ArchivedAppointment.deleted_at.desc()).all()
    return render_template('admin/archive.html', manual_deleted=manual, auto_deleted=auto)

@bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_status(id):
    data = request.get_json()
    appointment = Appointment.query.get_or_404(id)
    action = data.get('action')
    note = data.get('note', '')

    if action == 'confirm':
        appointment.status = 'підтверджено'
        template = 'email/confirmed.html'
        subject = "Заявку підтверджено"
    else:
        appointment.status = 'відхилено'
        template = 'email/rejected.html'
        subject = "Скасування запису"
    
    db.session.commit()

    try:
        msg = Message(subject,
                      sender=current_app.config.get('MAIL_USERNAME'),
                      recipients=[appointment.client.email])
        
        msg.html = render_template(template, appointment=appointment, note=note)
        
        mail.send(msg)
        print(f"--- HTML MAIL SENT USING {template} ---")
    except Exception as e:
        print(f"--- MAIL ERROR: {str(e)} ---")

    return jsonify({'status': 'success', 'new_status': appointment.status})

@bp.route('/delete_appointment/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_appointment(id):
    app = Appointment.query.get_or_404(id)
    archive_entry = ArchivedAppointment(
        original_id=app.id,
        client_name=app.client.name,
        client_email=app.client.email,
        service_name=app.service.name,
        slot_info=f"{app.slot.date.strftime('%d.%m.%Y')} {app.slot.start_time.strftime('%H:%M')}",
        status=app.status,
        deletion_type='manual'
    )
    if app.slot:
        app.slot.is_booked = False
    db.session.add(archive_entry)
    db.session.delete(app)
    db.session.commit()
    return jsonify({'status': 'success'})