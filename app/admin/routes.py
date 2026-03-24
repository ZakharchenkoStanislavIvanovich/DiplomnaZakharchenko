from datetime import datetime, timedelta
from flask import render_template, abort, request, jsonify, current_app
from flask_login import login_required, current_user
from app.admin import bp
from app.models import Appointment, ArchivedAppointment, TimeSlot, Service
from app import db, mail
from functools import wraps
from flask_mail import Message
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from app.utils import encrypt_data, decrypt_data

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def cleanup_tasks():
    now = datetime.now() 
    one_day_ago = now - timedelta(days=1)
    all_rejected = Appointment.query.filter(
        Appointment._status == encrypt_data('відхилено')
    ).all()
    
    to_archive = [a for a in all_rejected if a.created_at <= one_day_ago]
    
    for app in to_archive:
        submitted_at = app.created_at.strftime('%d.%m %H:%M')
        
        archive_entry = ArchivedAppointment(
            original_id=app.slot_id,
            client_name=app.client.name,
            client_email=app.client.email,
            client_phone=app.client.phone,
            service_name=app.service.name,
            slot_info=f"{app.slot.date.strftime('%d.%m.%Y')} {app.slot.start_time.strftime('%H:%M')} | {submitted_at}",
            status=app.status,
            deletion_type='automatic'
        )
        if app.slot:
            app.slot.is_booked = False
        db.session.add(archive_entry)
        db.session.delete(app)
    
    three_days_ago = now - timedelta(days=3)
    ArchivedAppointment.query.filter(ArchivedAppointment.deleted_at <= three_days_ago).delete()
    db.session.commit()

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cleanup_tasks()
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()
    services = Service.query.all()
    services.sort(key=lambda x: x.name)
    all_slots = TimeSlot.query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    all_archived = ArchivedAppointment.query.all()

    calendar_data = defaultdict(list)
    for slot in all_slots:
        if slot.date.weekday() <= 4:
            date_key = slot.date.strftime('%Y-%m-%d')
            calendar_data[date_key].append(slot)
    
    return render_template('admin/dashboard.html', 
                            appointments=appointments, 
                            services=services,
                            calendar_data=dict(calendar_data),
                            all_archived=all_archived,
                            relativedelta=relativedelta,
                            now=datetime.now())

@bp.route('/archive')
@login_required
@admin_required
def archive():
    cleanup_tasks()
    all_archived = ArchivedAppointment.query.order_by(ArchivedAppointment.deleted_at.desc()).all()
    
    manual = [a for a in all_archived if a.deletion_type == 'manual']
    auto = [a for a in all_archived if a.deletion_type == 'automatic']
    
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
        subject = "Відхилення запису"

    if appointment.slot:
        appointment.slot.is_booked = True
    
    db.session.commit()

    try:
        msg = Message(subject,
                      sender=current_app.config.get('MAIL_USERNAME'),
                      recipients=[appointment.client.email])
        msg.html = render_template(template, appointment=appointment, note=note)
        mail.send(msg)
    except Exception as e:
        print(f"--- MAIL ERROR: {str(e)} ---")

    return jsonify({'status': 'success', 'new_status': appointment.status})

@bp.route('/delete_appointment/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_appointment(id):
    app = Appointment.query.get_or_404(id)
    submitted_at = app.created_at.strftime('%d.%m %H:%M')
    
    archive_entry = ArchivedAppointment(
        original_id=app.slot_id,
        client_name=app.client.name,
        client_email=app.client.email,
        client_phone=app.client.phone,
        service_name=app.service.name,
        slot_info=f"{app.slot.date.strftime('%d.%m.%Y')} {app.slot.start_time.strftime('%H:%M')} | {submitted_at}",
        status=app.status,
        deletion_type='manual'
    )
    if app.slot:
        app.slot.is_booked = False
    db.session.add(archive_entry)
    db.session.delete(app)
    db.session.commit()
    return jsonify({'status': 'success'})


@bp.route('/services/add', methods=['POST'])
@login_required
@admin_required
def add_service():
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price', 0)
    new_service = Service(name=name, description=description, price=price)
    db.session.add(new_service)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/services/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    service.name = request.form.get('name')
    service.description = request.form.get('description')
    service.price = request.form.get('price', 0)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/services/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    if Appointment.query.filter_by(service_id=id).first():
        return jsonify({'status': 'error', 'message': 'На цю послугу є записи!'}), 400
    db.session.delete(service)
    db.session.commit()
    return jsonify({'status': 'success'})


@bp.route('/preview_slots', methods=['POST'])
@login_required
@admin_required
def preview_slots():
    data = request.get_json()
    date_str, start_t, end_t = data.get('date'), data.get('start_time'), data.get('end_time')
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    if dt.weekday() >= 5:
        return jsonify({'slots': [], 'message': 'Вихідні недоступні'}), 400
    interval = int(data.get('interval', 30))
    slots = []
    current_time = datetime.strptime(start_t, '%H:%M')
    end_dt = datetime.strptime(end_t, '%H:%M')
    while current_time < end_dt:
        slots.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=interval)
    return jsonify({'slots': slots, 'date': date_str})

@bp.route('/confirm_slots', methods=['POST'])
@login_required
@admin_required
def confirm_slots():
    data = request.get_json()
    target_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    for time_str in data.get('times', []):
        t = datetime.strptime(time_str, '%H:%M').time()
        existing = TimeSlot.query.filter_by(date=target_date, start_time=t).first()
        if not existing:
            db.session.add(TimeSlot(date=target_date, start_time=t, is_booked=False))
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/bulk_generate_slots', methods=['POST'])
@login_required
@admin_required
def bulk_generate_slots():
    data = request.get_json()
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    times = data['times']
    period = int(data['period'])
    days_generated = 0
    current_date = start_date
    while days_generated < period:
        if current_date.weekday() <= 4:
            for time_str in times:
                t = datetime.strptime(time_str, '%H:%M').time()
                if not TimeSlot.query.filter_by(date=current_date, start_time=t).first():
                    db.session.add(TimeSlot(date=current_date, start_time=t))
            days_generated += 1
        current_date += timedelta(days=1)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/delete_slots', methods=['POST'])
@login_required
@admin_required
def delete_multiple_slots():
    data = request.get_json()
    ids = data.get('ids', [])
    slots_to_delete = TimeSlot.query.filter(TimeSlot.id.in_(ids), TimeSlot.is_booked == False).all()
    for s in slots_to_delete:
        db.session.delete(s)
    db.session.commit()
    return jsonify({'status': 'success', 'deleted_count': len(slots_to_delete)})

@bp.route('/get_notifications')
@login_required
@admin_required
def get_notifications():
    try:
        notifications = []
        now = datetime.now()
        
        # Витягуємо ВСІ заявки і фільтруємо в Python (найнадійніший метод для шифрованих полів)
        all_apps = Appointment.query.all()
        pending_apps = [a for a in all_apps if a.status == 'очікує']
        
        new_items = []
        urgent_items = []
        for a in pending_apps:
            # Використовуємо розшифрований created_at
            upd_time = a.created_at if a.created_at else now
            diff = now - upd_time
            hours_passed = int(diff.total_seconds() // 3600)
            
            base_text = f"{a.client.name} | {a.service.name}"
            item_data = {'id': f"app_{a.id}", 'text': base_text, 'time': upd_time.strftime('%H:%M'), 'tab': 'apps'}
            
            if hours_passed >= 6:
                urgent_items.append(item_data)
            else:
                new_items.append(item_data)

        if urgent_items: notifications.append({'id': 'g_urgent', 'header': 'ТЕРМІНОВІ', 'items': urgent_items})
        if new_items: notifications.append({'id': 'g_new', 'header': 'Нові заявки', 'items': new_items})

        return jsonify({'details': notifications})
    except Exception as e:
        print(f"NOTIF ERROR: {e}")
        return jsonify({'error': str(e)}), 500