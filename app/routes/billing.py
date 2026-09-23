from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import db, Invoice, Payment
from ..utils import log_action

bp = Blueprint("billing", __name__)


@bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    query = Invoice.query
    if status:
        query = query.filter_by(status=status)
    invoices = query.order_by(Invoice.issued_date.desc()).all()
    return render_template("billing/index.html", invoices=invoices, status=status)


@bp.route("/<int:invoice_id>")
@login_required
def view(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("billing/view.html", invoice=invoice)


@bp.route("/<int:invoice_id>/pay", methods=["POST"])
@login_required
def pay(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    amount = float(request.form.get("amount") or 0)

    if amount <= 0:
        flash("Enter a valid payment amount.", "danger")
        return redirect(url_for("billing.view", invoice_id=invoice_id))

    payment = Payment(
        invoice_id=invoice.id,
        amount=amount,
        method=request.form.get("method", "Cash"),
        reference=request.form.get("reference"),
        received_by_id=current_user.id,
    )
    db.session.add(payment)

    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.total:
        invoice.status = "Paid"
    elif invoice.amount_paid > 0:
        invoice.status = "Partially Paid"

    db.session.commit()
    log_action("CREATE", "Payment", payment.id, f"{amount} on invoice {invoice.invoice_number}")
    flash(f"Payment of {amount:.2f} recorded.", "success")
    return redirect(url_for("billing.view", invoice_id=invoice_id))


@bp.route("/<int:invoice_id>/discount", methods=["POST"])
@login_required
def apply_discount(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    discount = float(request.form.get("discount") or 0)
    invoice.discount = discount
    invoice.total = max(invoice.subtotal - discount + invoice.tax, 0)
    db.session.commit()
    log_action("UPDATE", "Invoice", invoice.id, f"discount set to {discount}")
    flash("Discount applied.", "success")
    return redirect(url_for("billing.view", invoice_id=invoice_id))
