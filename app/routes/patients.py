from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from ..models import db, Patient, Doctor
from ..utils import generate_code, log_action, parse_date

bp = Blueprint("patients", __name__)


@bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
                Patient.patient_code.ilike(like),
                Patient.phone.ilike(like),
            )
        )
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("patients/index.html", patients=patients, q=q)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    doctors = Doctor.query.filter_by(active=True).order_by(Doctor.full_name).all()
    if request.method == "POST":
        patient = Patient(
            patient_code=generate_code("PT", Patient, "patient_code"),
            first_name=request.form["first_name"].strip(),
            last_name=request.form["last_name"].strip(),
            date_of_birth=parse_date(request.form.get("date_of_birth")),
            gender=request.form.get("gender"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            address=request.form.get("address"),
            city=request.form.get("city"),
            blood_group=request.form.get("blood_group"),
            allergies=request.form.get("allergies"),
            medical_notes=request.form.get("medical_notes"),
            emergency_contact_name=request.form.get("emergency_contact_name"),
            emergency_contact_phone=request.form.get("emergency_contact_phone"),
            referring_doctor_id=request.form.get("referring_doctor_id") or None,
        )
        db.session.add(patient)
        db.session.commit()
        log_action("CREATE", "Patient", patient.id, patient.full_name)
        flash(f"Patient {patient.full_name} registered ({patient.patient_code}).", "success")
        return redirect(url_for("patients.view", patient_id=patient.id))

    return render_template("patients/form.html", patient=None, doctors=doctors)


@bp.route("/<int:patient_id>")
@login_required
def view(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    orders = patient.lab_orders.order_by(db.desc("order_date")).all()
    invoices = patient.invoices.order_by(db.desc("issued_date")).all()
    return render_template("patients/view.html", patient=patient, orders=orders, invoices=invoices)


@bp.route("/<int:patient_id>/edit", methods=["GET", "POST"])
@login_required
def edit(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    doctors = Doctor.query.filter_by(active=True).order_by(Doctor.full_name).all()

    if request.method == "POST":
        patient.first_name = request.form["first_name"].strip()
        patient.last_name = request.form["last_name"].strip()
        patient.date_of_birth = parse_date(request.form.get("date_of_birth"))
        patient.gender = request.form.get("gender")
        patient.phone = request.form.get("phone")
        patient.email = request.form.get("email")
        patient.address = request.form.get("address")
        patient.city = request.form.get("city")
        patient.blood_group = request.form.get("blood_group")
        patient.allergies = request.form.get("allergies")
        patient.medical_notes = request.form.get("medical_notes")
        patient.emergency_contact_name = request.form.get("emergency_contact_name")
        patient.emergency_contact_phone = request.form.get("emergency_contact_phone")
        patient.referring_doctor_id = request.form.get("referring_doctor_id") or None
        db.session.commit()
        log_action("UPDATE", "Patient", patient.id, patient.full_name)
        flash("Patient updated.", "success")
        return redirect(url_for("patients.view", patient_id=patient.id))

    return render_template("patients/form.html", patient=patient, doctors=doctors)


@bp.route("/<int:patient_id>/delete", methods=["POST"])
@login_required
def delete(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    name = patient.full_name
    db.session.delete(patient)
    db.session.commit()
    log_action("DELETE", "Patient", patient_id, name)
    flash(f"Patient {name} deleted.", "info")
    return redirect(url_for("patients.index"))
