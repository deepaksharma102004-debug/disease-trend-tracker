from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from modules.data_manager import (
    load_all_patients, get_patient,
    load_patient_diseases, add_patient, add_disease,
    add_visit, load_disease_visits, get_disease_parameters,
    delete_patient_cascade
)
from modules.trend_engine import detect_trend, get_risk_badge
from modules.ai_advisor import get_ai_recommendation
from modules.ml_model import forecast_next_3
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
csrf = CSRFProtect(app)

from modules.db import db
from modules.models import Doctor, Patient, Disease, Visit

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()


def check_login():
    return session.get("doctor_id") is not None

def is_own_patient(patient_id):
    """Checks whether the patient_id belongs to the logged-in doctor"""
    patients = load_all_patients(session["doctor_id"])
    return patient_id in [p["patient_id"] for p in patients]

def load_doctors():
    doctors = Doctor.query.all()
    return [
        {"doctor_id": d.doctor_id, "doctor_name": d.doctor_name,
         "username": d.username, "password": d.password}
        for d in doctors
    ]

def _cleanup_failed_patient(patient_id):
    """Best-effort rollback: removes a patient left half-created after
    add-patient fails partway through. Never lets a cleanup error mask
    the original error being handled."""
    try:
        db.session.rollback()
        delete_patient_cascade(patient_id)
    except Exception:
        db.session.rollback()


# ── Auth Routes ───────────────────────────────────────

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if check_login():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        for doctor in load_doctors():
            if doctor["username"] == username and check_password_hash(doctor["password"], password):
                session["doctor_id"]   = doctor["doctor_id"]
                session["doctor_name"] = doctor["doctor_name"]
                return redirect(url_for("dashboard"))
    return redirect(url_for("home"))

@app.route("/api/login", methods=["POST"])
def api_login():
    body = request.get_json()
    for doctor in load_doctors():
        if doctor["username"] == body["username"] and check_password_hash(doctor["password"], body["password"]):
            session["doctor_id"]   = doctor["doctor_id"]
            session["doctor_name"] = doctor["doctor_name"]
            return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid username or password"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    error = success = None
    if request.method == "POST":
        doctor_name = request.form.get("doctor_name")
        username    = request.form.get("username")
        password    = request.form.get("password")
        doctors     = load_doctors()
        if any(d["username"] == username for d in doctors):
            error = "❌ Username already exists"
        else:
            new_id  = f"D00{len(doctors) + 1}"
            db.session.add(Doctor(
                doctor_id=new_id,
                doctor_name=doctor_name,
                username=username,
                password=generate_password_hash(password)
            ))
            db.session.commit()
            success = "✅ Registration successful! Please login."
    return render_template("register.html", error=error, success=success)


# ── Dashboard ─────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if not check_login():
        return redirect(url_for("home"))

    raw_patients = load_all_patients(session["doctor_id"])
    patients = []
    high_risk_count = 0
    improving_count = 0
    visits_this_month = 0
    current_month = datetime.now().strftime("%Y-%m")

    for p in raw_patients:
        pid = p["patient_id"]
        diseases = load_patient_diseases(pid)
        disease_summaries = []
        worst_risk = "LOW"
        last_visit_date = None

        for disease in diseases:
            did = disease["disease_id"]
            parameters = get_disease_parameters(did)
            visits = sorted(load_disease_visits(pid, did), key=lambda x: x["visit_date"])
            if not visits:
                continue

            param_trends = {}
            for param in parameters:
                values = [v.get(param) for v in visits if v.get(param) is not None]
                param_trends[param] = detect_trend(values)

            trend_values = list(param_trends.values())
            risk = get_risk_badge(
                trend_values[0] if len(trend_values) > 0 else "stable",
                trend_values[1] if len(trend_values) > 1 else "stable"
            )

            if risk == "HIGH":
                worst_risk = "HIGH"
            elif risk == "IMPROVING" and worst_risk != "HIGH":
                worst_risk = "IMPROVING"
            elif worst_risk not in ("HIGH", "IMPROVING"):
                worst_risk = "STABLE"

            latest_visit = visits[-1]
            first_param  = parameters[0] if parameters else None

            disease_summaries.append({
                "disease_id":        did,
                "disease_name":      disease["disease_name"],
                "risk":              risk,
                "first_param":       first_param,
                "first_param_value": latest_visit.get(first_param) if first_param else None,
                "trend":             param_trends.get(first_param, "stable") if first_param else "stable"
            })

            if not last_visit_date or latest_visit["visit_date"] > last_visit_date:
                last_visit_date = latest_visit["visit_date"]

            for v in visits:
                if v["visit_date"][:7] == current_month:
                    visits_this_month += 1

        if worst_risk == "HIGH":
            high_risk_count += 1
        elif worst_risk == "IMPROVING":
            improving_count += 1

        patients.append({
            "patient_id":   pid,
            "patient_name": p["patient_name"],
            "diseases":     disease_summaries,
            "worst_risk":   worst_risk,
            "last_visit":   last_visit_date or "—"
        })

    stats = {
        "total":              len(patients),
        "high_risk":          high_risk_count,
        "improving":          improving_count,
        "visits_this_month":  visits_this_month
    }

    return render_template("index.html",
        patients=patients,
        doctor_name=session["doctor_name"],
        stats=stats
    )


# ── Patient Detail (disease tabs) ────────────────────

@app.route("/patient/<patient_id>")
def patient_detail(patient_id):
    if not check_login():
        return redirect(url_for("home"))

    if not is_own_patient(patient_id):
        # return "Access denied — this patient does not belong to you", 403
        return jsonify({"status": "error", "message": "Patient not found"}), 403

    patient  = get_patient(patient_id)
    diseases = load_patient_diseases(patient_id)
    months   = request.args.get("months", "6")

    disease_data = []
    for disease in diseases:
        did        = disease["disease_id"]
        parameters = get_disease_parameters(did)
        visits     = load_disease_visits(patient_id, did)

        # Sort aur filter
        visits = sorted(visits, key=lambda x: x["visit_date"])
        if months != "all":
            visits = visits[-int(months):]

        if not visits:
            continue

        # Har parameter ke liye trend + forecast
        param_trends    = {}
        param_forecasts = {}
        for param in parameters:
            values = [v.get(param) for v in visits if v.get(param) is not None]
            param_trends[param]    = detect_trend(values)
            param_forecasts[param] = forecast_next_3(values)

        # Risk badge — pehle 2 parameter se
        trend_values = list(param_trends.values())
        risk = get_risk_badge(
            trend_values[0] if len(trend_values) > 0 else "stable",
            trend_values[1] if len(trend_values) > 1 else "stable"
        )

        # AI recommendation
        try:
            ai_rec = get_ai_recommendation(
                patient["patient_name"],
                disease["disease_name"],
                param_trends,
                {p: [v.get(p) for v in visits if v.get(p) is not None] for p in parameters}
            )
        except Exception:
            ai_rec = "⚠️ AI recommendation temporarily unavailable."

        disease_data.append({
            "disease_id":   did,
            "disease_name": disease["disease_name"],
            "parameters":   parameters,
            "visits":       visits,
            "trends":       param_trends,
            "forecasts":    param_forecasts,
            "risk":         risk,
            "ai_rec":       ai_rec
        })

    return render_template("patient.html",
        patient=patient,
        disease_data=disease_data,
        months=months
    )


# ── API: Add Patient ──────────────────────────────────

@app.route("/api/add-patient", methods=["POST"])
def api_add_patient():
    if not check_login():
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    body         = request.get_json()
    patient_id   = body.get("patient_id", "").strip()
    patient_name = body.get("patient_name", "").strip()
    diseases     = body.get("diseases", [])

    if not patient_id or not patient_name or not diseases:
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    if Patient.query.get(patient_id):
        return jsonify({"status": "error", "message": "Patient ID already exists"}), 409

    try:
        add_patient(patient_id, patient_name, session["doctor_id"])
        for d in diseases:
            disease_id = add_disease(patient_id, d["disease_name"], d["parameters"])
            add_visit(patient_id, disease_id, d["visit_date"], d["param_values"])
        return jsonify({"status": "success"})
    except ValueError as e:
        _cleanup_failed_patient(patient_id)
        return jsonify({"status": "error", "message": str(e)}), 409
    except Exception as e:
        _cleanup_failed_patient(patient_id)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/next-patient-id")
def api_next_patient_id():
    if not check_login():
        return jsonify({"status": "error"}), 401
    next_num = Patient.query.count() + 1
    next_id  = f"P{str(next_num).zfill(3)}"
    return jsonify({"patient_id": next_id})


# ── API: Add Disease to existing patient ──────────────

@app.route("/api/add-disease", methods=["POST"])
def api_add_disease():
    if not check_login():
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    body         = request.get_json()
    patient_id   = body.get("patient_id", "").strip()
    disease_name = body.get("disease_name", "").strip()
    parameters   = body.get("parameters", [])

    if not all([patient_id, disease_name, parameters]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    if not is_own_patient(patient_id):
        return jsonify({"status": "error", "message": "Patient not found"}), 403

    try:
        disease_id = add_disease(patient_id, disease_name, parameters)
        return jsonify({"status": "success", "disease_id": disease_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── API: Add Visit ────────────────────────────────────

@app.route("/api/add-visit", methods=["POST"])
def api_add_visit():
    if not check_login():
        return jsonify({"status": "error", "message": "Not logged in"}), 401

    body         = request.get_json()
    patient_id   = body.get("patient_id", "").strip()
    disease_id   = body.get("disease_id", "").strip()
    visit_date   = body.get("visit_date", "").strip()
    param_values = body.get("param_values", {})  # {"HbA1c": 8.2}

    if not all([patient_id, disease_id, visit_date, param_values]):
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    # Patient is doctor ka hai?
    if not is_own_patient(patient_id):
        return jsonify({"status": "error", "message": "Patient not found"}), 403

    try:
        add_visit(patient_id, disease_id, visit_date, param_values)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── API: Get patient diseases (for visit modal) ───────

@app.route("/api/patient-diseases/<patient_id>")
def api_patient_diseases(patient_id):
    if not check_login():
        return jsonify({"status": "error"}), 401

    if not is_own_patient(patient_id):
        return jsonify({"status": "error", "message": "Patient not found"}), 403
    
    diseases = load_patient_diseases(patient_id)
    # Parameters bhi saath mein bhejo
    for d in diseases:
        d["parameters"] = d["parameters"].split("|")
    return jsonify(diseases)


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug_mode, host="0.0.0.0", port=port)