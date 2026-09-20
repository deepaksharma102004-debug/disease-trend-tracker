from modules.db import db

class Doctor(db.Model):
    __tablename__ = "doctors"

    doctor_id   = db.Column(db.String(10), primary_key=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    username    = db.Column(db.String(50), unique=True, nullable=False)
    password    = db.Column(db.String(255), nullable=False)


class Patient(db.Model):
    __tablename__ = "patients"

    patient_id   = db.Column(db.String(10), primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    doctor_id    = db.Column(db.String(10), db.ForeignKey("doctors.doctor_id"), nullable=False)


class Disease(db.Model):
    __tablename__ = "patient_diseases"

    disease_id   = db.Column(db.String(20), primary_key=True)
    patient_id   = db.Column(db.String(10), db.ForeignKey("patients.patient_id"), nullable=False)
    disease_name = db.Column(db.String(100), nullable=False)
    parameters   = db.Column(db.String(255), nullable=False)


class Visit(db.Model):
    __tablename__ = "patient_visits"

    visit_id        = db.Column(db.String(20), primary_key=True)
    patient_id      = db.Column(db.String(10), db.ForeignKey("patients.patient_id"), nullable=False)
    disease_id      = db.Column(db.String(20), db.ForeignKey("patient_diseases.disease_id"), nullable=False)
    visit_date      = db.Column(db.Date, nullable=False)
    parameter_name  = db.Column(db.String(50), nullable=False)
    parameter_value = db.Column(db.Float, nullable=False)