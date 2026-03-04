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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --- СИСТЕМНІ ФУНКЦІЇ ОЧИЩЕННЯ ---

def cleanup_tasks():
    now = datetime.utcnow()
    
    one_day_ago = now - timedelta(days=1)
    to_archive = Appointment.query.filter(
        Appointment.status == 'відхилено',
        Appointment.updated_at <= one_day_ago
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
    
    five_days_ago = now - timedelta(days=5)
    ArchivedAppointment.query.filter(ArchivedAppointment.deleted_at <= five_days_ago).delete()
    
    db.session.commit()

# --- РОУТИ ПАНЕЛІ КЕРУВАННЯ ---

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cleanup_tasks()
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()
    services = Service.query.all()
    all_slots = TimeSlot.query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    calendar_data = defaultdict(list)
    for slot in all_slots:
        if slot.date.weekday() <= 4:
            date_key = slot.date.strftime('%Y-%m-%d')
            calendar_data[date_key].append(slot)
    
    return render_template('admin/dashboard.html', 
                           appointments=appointments, 
                           services=services,
                           calendar_data=dict(calendar_data),
                           relativedelta=relativedelta)

@bp.route('/archive')
@login_required
@admin_required
def archive():
    cleanup_tasks()
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

    # Логіка зміни статусу
    if action == 'confirm':
        appointment.status = 'підтверджено'
        template = 'email/confirmed.html'
        subject = "Заявку підтверджено"
    else:
        appointment.status = 'відхилено'
        template = 'email/rejected.html'
        subject = "Відхилення запису"

    # ГОЛОВНЕ ВИПРАВЛЕННЯ:
    # Незалежно від того, підтверджуєш ти чи відхиляєш (чи змінюєш рішення),
    # слот має бути ЗАБЛОКОВАНИМ (True) для нових клієнтів, 
    # бо там уже висить ця заявка в базі.
    if appointment.slot:
        appointment.slot.is_booked = True
    
    db.session.commit()

    # Відправка пошти
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

# --- КЕРУВАННЯ ПОСЛУГАМИ ---

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

# --- КЕРУВАННЯ СЛОТАМИ ---

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
    # Також додаємо перевірку для ручного додавання
    data = request.get_json()
    target_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    if target_date.weekday() >= 5:
        return jsonify({'status': 'error', 'message': 'Неможливо створити слоти на вихідні'}), 400
    for time_str in data.get('times', []):
        t = datetime.strptime(time_str, '%H:%M').time()
        existing = TimeSlot.query.filter_by(date=target_date, start_time=t).first()
        if not existing:
            db.session.add(TimeSlot(date=target_date, start_time=t, is_booked=False))
        else:
            # Оновлюємо статус існуючого слота, якщо там є заявки
            if existing.appointments:
                existing.is_booked = True
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
                existing = TimeSlot.query.filter_by(date=current_date, start_time=t).first()
                
                if not existing:
                    db.session.add(TimeSlot(date=current_date, start_time=t, is_booked=False))
                else:
                    # ВИПРАВЛЕННЯ: Якщо слот існує і в ньому є БУДЬ-ЯКА заявка
                    # (очікує, підтверджена або відхилена), він МАЄ бути True.
                    if existing.appointments:
                        existing.is_booked = True
                    # Якщо ми перегенеровуємо порожні слоти, вони залишаються False
            
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

# --- СПОВІЩЕННЯ ---

# --- СПОВІЩЕННЯ (ВИПРАВЛЕНО) ---

@bp.route('/get_notifications')
@login_required
@admin_required
def get_notifications():
    try:
        notifications = []
        # Використовуємо локальний час (Україна — це UTC+2 або UTC+3)
        # Або просто datetime.now(), щоб збігалося з часом, який бачить нотаріус
        now = datetime.now() 
        today_date = now.date()
        urgent_flag = 0

        # 1. ЗАЯВКИ В ОЧІКУВАННІ (Нові та Термінові)
        pending_apps = Appointment.query.filter_by(status='очікує').all()
        for a in pending_apps:
            diff = now - a.updated_at
            hours_passed = diff.total_seconds() / 3600
            
            if hours_passed >= 6:
                urgent_flag = 1
                cycle = int(hours_passed // 6)
                notifications.append({
                    'id': f'stale_{a.id}_cycle_{cycle}',
                    'type': 'urgent',
                    'text': f"ТЕРМІНОВО: {a.client.name} чекає {int(hours_passed)} год! ({a.service.name})"
                })
            else:
                notifications.append({
                    'id': f'new_{a.id}',
                    'type': 'new',
                    'text': f"Нова заявка: {a.client.name} (на {a.slot.date.strftime('%d.%m')})"
                })

        # 2. ЗУСТРІЧІ НА СЬОГОДНІ
        now = datetime.now()
        today_date = now.date()
        today_str = today_date.strftime('%d.%m.%Y')
        
        all_active_apps = Appointment.query.join(TimeSlot).filter(
            Appointment.status.in_(['підтверджено', 'очікує'])
        ).all()

        today_apps = [a for a in all_active_apps if a.slot.date == today_date]
        today_apps.sort(key=lambda x: x.slot.start_time)

        if today_apps:
            notifications.append({
                'id': f'today_group_{today_date.strftime("%Y%m%d")}',
                'type': 'today_header',
                'text': f"Сьогодні ({today_str}) заплановано зустрічей: {len(today_apps)}",
                'sub_items': [
                    {
                        'slot_id': a.slot.id,
                        'monday_key': (a.slot.date - relativedelta(days=a.slot.date.weekday())).strftime('%Y-%m-%d'),
                        'text': f"{a.slot.start_time.strftime('%H:%M')} - {a.client.name}"
                    } for a in today_apps
                ]
            })

        # 3. АВТОМАТИЧНО ВИДАЛЕНІ (за останні 12 годин)
        twelve_hours_ago = now - timedelta(hours=12)
        deleted = ArchivedAppointment.query.filter(
            ArchivedAppointment.deletion_type == 'automatic',
            ArchivedAppointment.deleted_at >= twelve_hours_ago
        ).all()

        if deleted:
            notifications.append({
                'id': f'auto_del_summary_{len(deleted)}',
                'type': 'info',
                'text': f"{len(deleted)} відхилених заявок видалено автоматично"
            })

        return jsonify({
            'total': len(notifications),
            'urgent': urgent_flag,
            'details': notifications
        })

    except Exception as e:
        print(f"Помилка сповіщень: {e}")
        return jsonify({'error': str(e)}), 500