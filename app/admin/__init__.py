from flask import Blueprint

bp = Blueprint('admin', __name__)

from app.main import routes
