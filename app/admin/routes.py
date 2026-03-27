import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import render_template, abort, request, jsonify, current_app, url_for, redirect, flash
from flask_login import login_required, current_user
from app.admin import bp
from app.models import Appointment, ArchivedAppointment, TimeSlot, Service, NotaryPhoto
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
    
    archived_map = {str(ar.original_id): ar for ar in all_archived}

    calendar_data = defaultdict(list)
    for slot in all_slots:
        if slot.date.weekday() <= 4:
            date_key = slot.date.strftime('%Y-%m-%d')
            calendar_data[date_key].append(slot)
    
    return render_template('admin/dashboard.html', 
                            appointments=appointments, 
                            services=services,
                            calendar_data=dict(calendar_data),
                            archived_map=archived_map,
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
        today_date = now.date()
        
        cleanup_tasks()
        all_apps = Appointment.query.all()
        
        today_apps = [a for a in all_apps if a.slot.date == today_date and a.status == 'підтверджено']
        if today_apps:
            today_items = []
            for a in today_apps:
                monday = a.slot.date - timedelta(days=a.slot.date.weekday())
                today_items.append({
                    'id': f"today_{a.id}",
                    'text': f"{a.slot.start_time.strftime('%H:%M')} - {a.client.name}",
                    'time': a.slot.start_time.strftime('%H:%M'),
                    'tab': 'calendar',
                    'slot_id': a.slot.id,
                    'monday_key': monday.strftime('%Y-%m-%d')
                })
            notifications.append({
                'id': 'g_today',
                'header': 'План на сьогодні',
                'items': today_items
            })

        new_items = []
        urgent_items = []
        recommend_archive_items = []
        pending_clients = {}

        for a in all_apps:
            slot_dt = datetime.combine(a.slot.date, a.slot.start_time)
            upd_time = a.created_at if a.created_at else now
            
            if a.status == 'очікує':
                email = a.client.email
                if email not in pending_clients:
                    pending_clients[email] = []
                pending_clients[email].append(a)

                diff = now - upd_time
                hours_passed = int(diff.total_seconds() // 3600)
                item_data = {
                    'id': f"app_{a.id}", 
                    'text': f"{a.client.name} | {a.service.name}", 
                    'time': upd_time.strftime('%H:%M'), 
                    'tab': 'apps'
                }
                if hours_passed >= 6:
                    item_data['text'] = f"УВАГА: {a.client.name} чекає понад {hours_passed} год"
                    urgent_items.append(item_data)
                else:
                    new_items.append(item_data)
            
            elif a.status == 'підтверджено' and slot_dt < now:
                diff_past = now - slot_dt
                hours_past = int(diff_past.total_seconds() // 3600)
                if hours_past >= 6:
                    recommend_archive_items.append({
                        'id': f"rec_{a.id}",
                        'text': f"Завершено: {a.client.name} ({a.slot.date.strftime('%d.%m')})",
                        'time': a.slot.start_time.strftime('%H:%M'),
                        'tab': 'apps'
                    })

        duplicate_items = []
        for email, apps in pending_clients.items():
            if len(apps) > 1:
                duplicate_items.append({
                    'id': f"dup_{email}",
                    'text': f"Клієнт {apps[0].client.name} створив {len(apps)} заявки",
                    'time': now.strftime('%H:%M'),
                    'tab': 'apps'
                })
        if duplicate_items:
            notifications.append({'id': 'g_dups', 'header': 'Повторні заявки', 'items': duplicate_items})

        if urgent_items: notifications.append({'id': 'g_urgent', 'header': 'ТЕРМІНОВІ', 'items': urgent_items})
        if recommend_archive_items: notifications.append({'id': 'g_recommend', 'header': 'Рекомендовано до архіву', 'items': recommend_archive_items})
        if new_items: notifications.append({'id': 'g_new', 'header': 'Нові заявки', 'items': new_items})

        return jsonify({'details': notifications})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/upload_photo', methods=['POST'])
@login_required
@admin_required
def upload_photo():
    if 'photo' not in request.files:
        flash('Файл не знайдено', 'warning')
        return redirect(url_for('main.index'))
    
    file = request.files['photo']
    if file and file.filename != '':
        import shutil
        ext = os.path.splitext(file.filename)[1]
        random_name = f"{uuid.uuid4().hex}{ext}"
        
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'notary')
        
        os.makedirs(upload_path, exist_ok=True)

        try:
            full_path = os.path.join(upload_path, random_name)
            file.save(full_path)
            
            new_photo = NotaryPhoto(filename=random_name, is_active=False)
            db.session.add(new_photo)
            db.session.commit()
            flash('Фото завантажено успішно!', 'success')
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            flash(f'Критична помилка запису: {str(e)}', 'danger')
            
    return redirect(url_for('main.index'))

@bp.route('/photos/set_active/<int:photo_id>', methods=['POST'])
@login_required
@admin_required
def set_active_photo(photo_id):
    NotaryPhoto.query.update({NotaryPhoto.is_active: False})
    photo = NotaryPhoto.query.get_or_404(photo_id)
    photo.is_active = True
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/photos/delete/<int:photo_id>', methods=['POST'])
@login_required
@admin_required
def delete_photo(photo_id):
    photo = NotaryPhoto.query.get_or_404(photo_id)
    if photo.is_active:
        return jsonify({'status': 'error', 'message': 'Неможливо видалити активне фото'}), 400
    
    file_path = os.path.join(current_app.root_path, 'static', 'uploads', 'notary', photo.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(photo)
    db.session.commit()
    return jsonify({'status': 'success'})