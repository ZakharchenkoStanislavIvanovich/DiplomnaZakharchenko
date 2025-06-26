import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'supersecretkey'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')  # змінити на PostgreSQL при деплої
    SQLALCHEMY_TRACK_MODIFICATIONS = False