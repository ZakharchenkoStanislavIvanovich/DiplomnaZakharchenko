from flask import render_template
from app.main import bp
from app.models import Service

@bp.route('/')
def index():
    return render_template('main/index.html')

@bp.route('/contacts')
def contacts():
    return render_template('main/contacts.html')

@bp.route('/services')
def services_list():
    services = Service.query.order_by(Service.name.asc()).all()
    return render_template('main/services.html', services=services)