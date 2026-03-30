from flask import render_template
from app.main import bp
from app.models import Service, NotaryPhoto
from datetime import datetime

@bp.route('/')
def index():
    active_photo = NotaryPhoto.query.filter_by(is_active=True).first()
    all_photos = NotaryPhoto.query.all()
    all_photos.sort(key=lambda x: x.created_at if x.created_at else datetime.min, reverse=True)
    
    return render_template('main/index.html', 
                           active_photo=active_photo, 
                           all_photos=all_photos)

@bp.route('/services')
def services_list():
    services = Service.query.all()
    services.sort(key=lambda x: x.name)
    return render_template('main/services.html', services=services)