from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from ..models import db, Doctor
from ..utils import generate_code, log_action

bp = Blueprint("doctors", __name__)


@bp.route("/")
@login_required
def index():
    doctors = Doctor.query.order_by(Doctor.full_name).all()
    return render_template("doctors/index.html", doctors=doctors)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        doctor = Doctor(
            doctor_code=generate_code("DR", Doctor, "doctor_code"),
            full_name=request.form["full_name"].strip(),
            specialty=request.form.get("specialty"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            clinic_hospital=request.form.get("clinic_hospital"),
            commission_percent=float(request.form.get("commission_percent") or 0),
        )
        db.session.add(doctor)
        db.session.commit()
        log_action("CREATE", "Doctor", doctor.id, doctor.full_name)
        flash(f"Doctor {doctor.full_name} added.", "success")
        return redirect(url_for("doctors.index"))
    return render_template("doctors/form.html", doctor=None)


@bp.route("/<int:doctor_id>/edit", methods=["GET", "POST"])
@login_required
def edit(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == "POST":
        doctor.full_name = request.form["full_name"].strip()
        doctor.specialty = request.form.get("specialty")
        doctor.phone = request.form.get("phone")
        doctor.email = request.form.get("email")
        doctor.clinic_hospital = request.form.get("clinic_hospital")
        doctor.commission_percent = float(request.form.get("commission_percent") or 0)
        doctor.active = bool(request.form.get("active"))
        db.session.commit()
        log_action("UPDATE", "Doctor", doctor.id, doctor.full_name)
        flash("Doctor updated.", "success")
        return redirect(url_for("doctors.index"))
    return render_template("doctors/form.html", doctor=doctor)


@bp.route("/<int:doctor_id>/delete", methods=["POST"])
@login_required
def delete(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    name = doctor.full_name
    db.session.delete(doctor)
    db.session.commit()
    log_action("DELETE", "Doctor", doctor_id, name)
    flash(f"Doctor {name} removed.", "info")
    return redirect(url_for("doctors.index"))
