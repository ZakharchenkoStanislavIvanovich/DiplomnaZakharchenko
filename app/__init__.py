from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()

login.login_view = 'auth.login'
login.login_message = "Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки."
login.login_message_category = "info"

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.appointments import bp as appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/appointments')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app import models

    @login.user_loader
    def load_user(id):
        return models.User.query.get(int(id))

    return app