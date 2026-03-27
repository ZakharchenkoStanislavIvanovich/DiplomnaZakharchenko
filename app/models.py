from app import db
from flask_login import UserMixin
from datetime import datetime
from app.utils import encrypt_data, decrypt_data

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _username = db.Column('username', db.Text, unique=True, nullable=False)
    _email = db.Column('email', db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.String(512)) 
    is_admin = db.Column(db.Boolean, default=False)

    @property
    def username(self):
        return decrypt_data(self._username)
    @username.setter
    def username(self, value):
        self._username = encrypt_data(value)

    @property
    def email(self):
        return decrypt_data(self._email)
    @email.setter
    def email(self, value):
        self._email = encrypt_data(value)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column('name', db.Text, nullable=False)
    _email = db.Column('email', db.Text, nullable=False)
    _phone = db.Column('phone', db.Text, nullable=True)

    @property
    def name(self): return decrypt_data(self._name)
    @name.setter
    def name(self, value): self._name = encrypt_data(value)

    @property
    def email(self): return decrypt_data(self._email)
    @email.setter
    def email(self, value): self._email = encrypt_data(value)

    @property
    def phone(self): return decrypt_data(self._phone)
    @phone.setter
    def phone(self, value): self._phone = encrypt_data(value)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _name = db.Column('name', db.Text, nullable=False)
    _description = db.Column('description', db.Text)

    @property
    def name(self): return decrypt_data(self._name)
    @name.setter
    def name(self, value): self._name = encrypt_data(value)

    @property
    def description(self): return decrypt_data(self._description)
    @description.setter
    def description(self, value): self._description = encrypt_data(value)

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    _status = db.Column('status', db.Text, default=lambda: encrypt_data('очікує'))
    _created_at = db.Column('created_at', db.Text, default=lambda: encrypt_data(datetime.now().isoformat()))

    @property
    def status(self): 
        return decrypt_data(self._status)
    
    @status.setter
    def status(self, value): 
        self._status = encrypt_data(value)

    @property
    def created_at(self):
        try:
            if not self._created_at:
                return None
            return datetime.fromisoformat(decrypt_data(self._created_at))
        except Exception:
            return None

    @created_at.setter
    def created_at(self, value):
        if isinstance(value, datetime):
            self._created_at = encrypt_data(value.isoformat())
        else:
            self._created_at = encrypt_data(value)

    client = db.relationship("Client", backref="appointments")
    service = db.relationship("Service", backref="appointments")
    slot = db.relationship("TimeSlot", backref="appointments")

class ArchivedAppointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer)
    _client_name = db.Column('client_name', db.Text)
    _client_email = db.Column('client_email', db.Text)
    _client_phone = db.Column('client_phone', db.Text, nullable=True)
    _service_name = db.Column('service_name', db.Text)
    _slot_info = db.Column('slot_info', db.Text)
    _status = db.Column('status', db.Text)
    _deletion_type = db.Column('deletion_type', db.Text)
    deleted_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def client_name(self): return decrypt_data(self._client_name)
    @client_name.setter
    def client_name(self, value): self._client_name = encrypt_data(value)

    @property
    def client_email(self): return decrypt_data(self._client_email)
    @client_email.setter
    def client_email(self, value): self._client_email = encrypt_data(value)

    @property
    def client_phone(self): return decrypt_data(self._client_phone)
    @client_phone.setter
    def client_phone(self, value): self._client_phone = encrypt_data(value)

    @property
    def service_name(self): return decrypt_data(self._service_name)
    @service_name.setter
    def service_name(self, value): self._service_name = encrypt_data(value)

    @property
    def slot_info(self): return decrypt_data(self._slot_info)
    @slot_info.setter
    def slot_info(self, value): self._slot_info = encrypt_data(value)

    @property
    def status(self): return decrypt_data(self._status)
    @status.setter
    def status(self, value): self._status = encrypt_data(value)

    @property
    def deletion_type(self): return decrypt_data(self._deletion_type)
    @deletion_type.setter
    def deletion_type(self, value): self._deletion_type = encrypt_data(value)

class NotaryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    _filename = db.Column('filename', db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def filename(self):
        return decrypt_data(self._filename)

    @filename.setter
    def filename(self, value):
        self._filename = encrypt_data(value)