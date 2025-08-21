from app import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Client {self.name} - {self.email}>'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)  # <-- нове
    status = db.Column(db.String(20), default='очікує')

    client = db.relationship("Client", backref="appointments")
    service = db.relationship("Service", backref="appointments")
    slot = db.relationship("TimeSlot", backref="appointments")

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)              # для якої дати слот
    start_time = db.Column(db.Time, nullable=False)        # година початку
    is_booked = db.Column(db.Boolean, default=False)       # чи вже зайнятий