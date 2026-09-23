from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import db, Sample
from ..utils import log_action

bp = Blueprint("samples", __name__)


@bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    query = Sample.query
    if status:
        query = query.filter_by(status=status)
    samples = query.order_by(Sample.created_at.desc()).all()
    return render_template("samples/index.html", samples=samples, status=status)


@bp.route("/<int:sample_id>/collect", methods=["POST"])
@login_required
def collect(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    sample.status = "Collected"
    sample.collection_datetime = datetime.utcnow()
    sample.collected_by_id = current_user.id
    db.session.commit()

    # Bump parent order status if it was still Pending
    order = sample.lab_order
    if order.status == "Pending":
        order.status = "Sample Collected"
        db.session.commit()

    log_action("UPDATE", "Sample", sample.id, "collected")
    flash(f"Sample {sample.sample_id} marked as collected.", "success")
    return redirect(url_for("samples.index"))


@bp.route("/<int:sample_id>/receive", methods=["POST"])
@login_required
def receive(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    sample.status = "Received in Lab"
    db.session.commit()

    order = sample.lab_order
    if order.status in ("Pending", "Sample Collected"):
        order.status = "In Progress"
        db.session.commit()

    log_action("UPDATE", "Sample", sample.id, "received in lab")
    flash(f"Sample {sample.sample_id} received in lab.", "success")
    return redirect(url_for("samples.index"))


@bp.route("/<int:sample_id>/reject", methods=["POST"])
@login_required
def reject(sample_id):
    sample = Sample.query.get_or_404(sample_id)
    sample.status = "Rejected"
    sample.rejection_reason = request.form.get("reason", "")
    db.session.commit()
    log_action("UPDATE", "Sample", sample.id, f"rejected: {sample.rejection_reason}")
    flash(f"Sample {sample.sample_id} rejected.", "warning")
    return redirect(url_for("samples.index"))
