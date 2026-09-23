from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import db, LabOrderTest, Result, LabOrder
from ..utils import log_action

bp = Blueprint("results", __name__)


@bp.route("/")
@login_required
def index():
    """Worklist of order-tests awaiting result entry."""
    pending = (
        LabOrderTest.query
        .join(LabOrder)
        .filter(LabOrder.status.in_(["In Progress", "Sample Collected"]))
        .order_by(LabOrder.order_date.desc())
        .all()
    )
    return render_template("results/index.html", pending=pending)


@bp.route("/entry/<int:order_test_id>", methods=["GET", "POST"])
@login_required
def entry(order_test_id):
    order_test = LabOrderTest.query.get_or_404(order_test_id)
    result = order_test.result or Result(lab_order_test_id=order_test.id)

    if request.method == "POST":
        result.value = request.form.get("value")
        result.unit = request.form.get("unit") or order_test.test.unit
        result.reference_range = request.form.get("reference_range") or order_test.test.reference_range
        result.flag = request.form.get("flag", "Normal")
        result.notes = request.form.get("notes")
        result.performed_by_id = current_user.id
        result.performed_at = datetime.utcnow()
        result.status = "Entered"

        if not result.id:
            db.session.add(result)

        order_test.status = "Result Entered"
        db.session.commit()

        log_action("CREATE" if not result.id else "UPDATE", "Result", result.id,
                    f"{order_test.test.name} = {result.value}")
        flash(f"Result recorded for {order_test.test.name}.", "success")
        return redirect(url_for("results.index"))

    return render_template("results/entry.html", order_test=order_test, result=result)


@bp.route("/verify/<int:result_id>", methods=["POST"])
@login_required
def verify(result_id):
    result = Result.query.get_or_404(result_id)
    result.status = "Verified"
    result.verified_by_id = current_user.id
    result.verified_at = datetime.utcnow()
    db.session.commit()

    order_test = result.order_test
    order_test.status = "Verified"

    # If every test on the order has a verified result, mark order Completed
    order = order_test.lab_order
    all_verified = all(
        ot.result and ot.result.status == "Verified"
        for ot in order.tests.all()
    )
    if all_verified:
        order.status = "Completed"
    db.session.commit()

    log_action("UPDATE", "Result", result.id, "verified")
    flash("Result verified.", "success")
    return redirect(url_for("lab_orders.view", order_id=order.id))
