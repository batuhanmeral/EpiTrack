import datetime
from app.extensions import db


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    tcno = db.Column(db.String(11), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    patients = db.relationship('Patient', backref='doctor', lazy=True)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    tcno = db.Column(db.String(11), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    bloodtype = db.Column(db.String(5))
    birthdate = db.Column(db.Date)
    doctorid = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    seizures = db.relationship('Seizure', backref='patient', lazy=True, cascade="all, delete-orphan")


class Seizure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patientid = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    seizuretime = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50))
    trigger = db.Column(db.String(100))
    postictal = db.Column(db.String(200))
    duration = db.Column(db.Integer)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    sender_role = db.Column(db.String(10), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    doctor = db.relationship('Doctor', backref=db.backref('messages', cascade='all, delete-orphan'))
    patient = db.relationship('Patient', backref=db.backref('messages', cascade='all, delete-orphan'))


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    actor_role = db.Column(db.String(10))
    actor_id = db.Column(db.Integer)
    actor_name = db.Column(db.String(100))
    action = db.Column(db.String(20))
    entity = db.Column(db.String(30))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.String(255))
