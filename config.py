import os
import sys

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        db_url = db_url.strip()
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        SQLALCHEMY_DATABASE_URI = None 
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    _mail_port = os.environ.get('MAIL_PORT')
    MAIL_PORT = int(_mail_port.strip()) if _mail_port and _mail_port.strip() else None
    _mail_tls = os.environ.get('MAIL_USE_TLS', 'True')
    MAIL_USE_TLS = _mail_tls.lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')