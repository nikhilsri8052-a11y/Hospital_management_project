from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from datetime import datetime, date, time

db = SQLAlchemy()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from app.models import Admin, Doctor, Patient
    user = Admin.query.get(int(user_id))
    if user:
        return user
    user = Doctor.query.get(int(user_id))
    if user:
        return user
    user = Patient.query.get(int(user_id))
    return user

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class specialization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    about = db.Column(db.Text, nullable=False)
    doctors = db.relationship('Doctor', backref='specialization', cascade='all, delete-orphan')

class Doctor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specialization.id', ondelete='CASCADE'), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    education = db.Column(db.String(250))
    blacklisted = db.Column(db.Boolean, default=False)
    slots = db.relationship('DoctorSlot', backref='doctor', cascade='all, delete-orphan', passive_deletes=True)
    appointments = db.relationship('Appointment', backref='doctor', cascade='all, delete-orphan', passive_deletes=True)

class blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    date_blacklisted = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True)
    phone = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    dob = db.Column(db.Date)
    address = db.Column(db.Text)
    blood_group = db.Column(db.String(5))
    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_phone = db.Column(db.String(20))
    added_on = db.Column(db.DateTime, default=datetime.utcnow)
    password = db.Column(db.String(150), nullable=False)
    history = db.relationship('PatientHistory', backref='patient', cascade='all, delete-orphan', passive_deletes=True)
    appointments = db.relationship('Appointment', backref='patient', cascade='all, delete-orphan', passive_deletes=True)

class PatientHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    notes = db.Column(db.Text)

class DoctorSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slot_name = db.Column(db.String(20))
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_patients = db.Column(db.Integer, default=5)
    current_patients = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Available')
    appointments = db.relationship('Appointment', backref='slot', cascade='all, delete-orphan', passive_deletes=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id', ondelete='CASCADE'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('doctor_slot.id', ondelete='CASCADE'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    booked_on = db.Column(db.DateTime, default=datetime.utcnow)

class BlacklistedPatient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    reason = db.Column(db.Text, nullable=False)
    date_blacklisted = db.Column(db.DateTime, default=datetime.utcnow)