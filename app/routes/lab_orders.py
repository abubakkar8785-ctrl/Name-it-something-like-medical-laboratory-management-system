from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import db, LabOrder, LabOrderTest, Patient, Doctor, TestCatalog, Sample, Invoice
from ..utils import generate_code, log_action

bp = Blueprint("lab_orders", __name__)


@bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    query = LabOrder.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(LabOrder.order_date.desc()).all()
    return render_template("lab_orders/index.html", orders=orders, status=status)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    patients = Patient.query.order_by(Patient.first_name).all()
    doctors = Doctor.query.filter_by(active=True).order_by(Doctor.full_name).all()
    tests = TestCatalog.query.filter_by(active=True).order_by(TestCatalog.category, TestCatalog.name).all()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        test_ids = request.form.getlist("test_ids")

        if not patient_id or not test_ids:
            flash("Select a patient and at least one test.", "danger")
            return render_template("lab_orders/form.html", patients=patients, doctors=doctors, tests=tests)

        order = LabOrder(
            order_number=generate_code("LO", LabOrder, "order_number"),
            patient_id=patient_id,
            doctor_id=request.form.get("doctor_id") or None,
            priority=request.form.get("priority", "Routine"),
            clinical_notes=request.form.get("clinical_notes"),
            created_by_id=current_user.id,
        )
        db.session.add(order)
        db.session.flush()

        subtotal = 0.0
        for tid in test_ids:
            catalog_item = TestCatalog.query.get(int(tid))
            if not catalog_item:
                continue
            order_test = LabOrderTest(
                lab_order_id=order.id,
                test_catalog_id=catalog_item.id,
                price_at_order=catalog_item.price,
            )
            subtotal += catalog_item.price
            db.session.add(order_test)

        # Auto-create one sample record per distinct sample type required
        sample_types = {
            TestCatalog.query.get(int(tid)).sample_type
            for tid in test_ids if TestCatalog.query.get(int(tid))
        }
        for stype in sample_types:
            if not stype:
                continue
            sample = Sample(
                sample_id=generate_code("SM", Sample, "sample_id"),
                lab_order_id=order.id,
                sample_type=stype,
                status="Pending Collection",
            )
            db.session.add(sample)

        # Auto-generate invoice
        invoice = Invoice(
            invoice_number=generate_code("INV", Invoice, "invoice_number"),
            patient_id=order.patient_id,
            lab_order_id=order.id,
            subtotal=subtotal,
            total=subtotal,
            created_by_id=current_user.id,
        )
        db.session.add(invoice)

        db.session.commit()
        log_action("CREATE", "LabOrder", order.id, order.order_number)
        flash(f"Lab order {order.order_number} created.", "success")
        return redirect(url_for("lab_orders.view", order_id=order.id))

    return render_template("lab_orders/form.html", patients=patients, doctors=doctors, tests=tests)


@bp.route("/<int:order_id>")
@login_required
def view(order_id):
    order = LabOrder.query.get_or_404(order_id)
    return render_template("lab_orders/view.html", order=order)


@bp.route("/<int:order_id>/status", methods=["POST"])
@login_required
def update_status(order_id):
    order = LabOrder.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status:
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()
        log_action("UPDATE", "LabOrder", order.id, f"status -> {new_status}")
        flash(f"Order status updated to {new_status}.", "success")
    return redirect(url_for("lab_orders.view", order_id=order.id))


@bp.route("/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel(order_id):
    order = LabOrder.query.get_or_404(order_id)
    order.status = "Cancelled"
    db.session.commit()
    log_action("UPDATE", "LabOrder", order.id, "cancelled")
    flash("Order cancelled.", "info")
    return redirect(url_for("lab_orders.view", order_id=order.id))
