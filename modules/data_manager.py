from modules.db import db
from modules.models import Patient, Disease, Visit
import uuid
from collections import defaultdict
from datetime import datetime

# ── Patients ──────────────────────────────────────────

def load_all_patients(doctor_id):
    patients = Patient.query.filter_by(doctor_id=doctor_id).all()
    return [
        {"patient_id": p.patient_id, "patient_name": p.patient_name, "doctor_id": p.doctor_id}
        for p in patients
    ]


def add_patient(patient_id, patient_name, doctor_id):
    if Patient.query.get(patient_id):
        raise ValueError("Patient ID already exists")
    db.session.add(Patient(patient_id=patient_id, patient_name=patient_name, doctor_id=doctor_id))
    db.session.commit()


def get_patient(patient_id):
    p = Patient.query.get(patient_id)
    if not p:
        return None
    return {"patient_id": p.patient_id, "patient_name": p.patient_name, "doctor_id": p.doctor_id}


# ── Diseases ──────────────────────────────────────────

def load_patient_diseases(patient_id):
    diseases = Disease.query.filter_by(patient_id=patient_id).all()
    return [
        {"disease_id": d.disease_id, "patient_id": d.patient_id,
         "disease_name": d.disease_name, "parameters": d.parameters}
        for d in diseases
    ]


def add_disease(patient_id, disease_name, parameters: list):
    disease_id = "DIS" + str(uuid.uuid4())[:6].upper()
    db.session.add(Disease(
        disease_id=disease_id,
        patient_id=patient_id,
        disease_name=disease_name,
        parameters="|".join(parameters)
    ))
    db.session.commit()
    return disease_id


def get_disease_parameters(disease_id):
    d = Disease.query.get(disease_id)
    if not d:
        return []
    return d.parameters.split("|")


# ── Visits ────────────────────────────────────────────

def add_visit(patient_id, disease_id, visit_date, param_values: dict):
    # Accept ISO date strings from the frontend ("YYYY-MM-DD") and coerce them
    # to real date objects instead of passing raw strings straight to the DB.
    if isinstance(visit_date, str):
        try:
            visit_date = datetime.strptime(visit_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"'{visit_date}' is not a valid date (expected YYYY-MM-DD)")

    for param_name, param_value in param_values.items():
        # A blank/missing value shouldn't crash the whole request — just skip it.
        if param_value is None or param_value == "":
            continue
        try:
            param_value = float(param_value)
        except (TypeError, ValueError):
            raise ValueError(f"'{param_value}' is not a valid number for {param_name}")

        visit_id = "V" + str(uuid.uuid4())[:8].upper()
        db.session.add(Visit(
            visit_id=visit_id,
            patient_id=patient_id,
            disease_id=disease_id,
            visit_date=visit_date,
            parameter_name=param_name,
            parameter_value=param_value
        ))
    db.session.commit()


def load_disease_visits(patient_id, disease_id):
    """
    Returns list of visits in wide format:
    [{"visit_date": "2024-01-15", "HbA1c": 8.2, "Fasting Sugar": 180}, ...]
    """
    visits = (
        Visit.query
        .filter_by(patient_id=patient_id, disease_id=disease_id)
        .order_by(Visit.visit_date)
        .all()
    )

    if not visits:
        return []

    # Long → wide format (manually, since ab pandas pivot nahi use kar rahe)
    grouped = defaultdict(dict)
    for v in visits:
        date_str = v.visit_date.strftime("%Y-%m-%d")
        grouped[date_str][v.parameter_name] = v.parameter_value

    result = []
    for date_str, params in grouped.items():
        row = {"visit_date": date_str}
        row.update(params)
        result.append(row)

    return result


def delete_patient_cascade(patient_id):
    """
    Removes a patient and everything linked to it (diseases, visits).
    Used to roll back a partially-created patient when add-patient fails
    midway (e.g. a bad disease/visit value after the patient row was
    already committed).
    """
    Visit.query.filter_by(patient_id=patient_id).delete()
    Disease.query.filter_by(patient_id=patient_id).delete()
    Patient.query.filter_by(patient_id=patient_id).delete()
    db.session.commit()