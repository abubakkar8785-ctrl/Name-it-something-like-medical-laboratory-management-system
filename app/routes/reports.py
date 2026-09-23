import os
from datetime import datetime
from flask import Blueprint, render_template, send_file, flash, redirect, url_for, request
from flask_login import login_required

from ..models import LabOrder, Invoice, Patient
from ..config import Config

bp = Blueprint("reports", __name__)


@bp.route("/")
@login_required
def index():
    completed_orders = LabOrder.query.filter_by(status="Completed").order_by(
        LabOrder.order_date.desc()
    ).all()
    return render_template("reports/index.html", orders=completed_orders)


@bp.route("/order/<int:order_id>/pdf")
@login_required
def order_pdf(order_id):
    order = LabOrder.query.get_or_404(order_id)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except ImportError:
        flash("PDF library not installed.", "danger")
        return redirect(url_for("lab_orders.view", order_id=order_id))

    filename = f"LabReport_{order.order_number}.pdf"
    filepath = os.path.join(Config.REPORTS_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, Config.APP_NAME)
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, "Laboratory Test Report")
    y -= 10 * mm

    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"Order #: {order.order_number}")
    c.drawString(110 * mm, y, f"Date: {order.order_date.strftime('%Y-%m-%d %H:%M')}")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Patient: {order.patient.full_name}  ({order.patient.patient_code})")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Age/Sex: {order.patient.age or '-'} / {order.patient.gender or '-'}")
    if order.ordering_doctor:
        y -= 6 * mm
        c.drawString(20 * mm, y, f"Referring Doctor: {order.ordering_doctor.full_name}")
    y -= 10 * mm

    # Table header
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "Test")
    c.drawString(90 * mm, y, "Result")
    c.drawString(120 * mm, y, "Unit")
    c.drawString(140 * mm, y, "Reference Range")
    c.drawString(180 * mm, y, "Flag")
    y -= 3 * mm
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 6 * mm

    c.setFont("Helvetica", 9)
    for ot in order.tests.all():
        if y < 30 * mm:
            c.showPage()
            y = height - 25 * mm
        r = ot.result
        c.drawString(20 * mm, y, ot.test.name[:35])
        c.drawString(90 * mm, y, (r.value if r else "-") or "-")
        c.drawString(120 * mm, y, (r.unit if r else "") or "")
        c.drawString(140 * mm, y, (r.reference_range if r else "") or "")
        flag = (r.flag if r else "") or ""
        if flag in ("High", "Low", "Critical"):
            c.setFillColor(colors.red)
        c.drawString(180 * mm, y, flag)
        c.setFillColor(colors.black)
        y -= 7 * mm

    y -= 10 * mm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, y, f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(20 * mm, y - 5 * mm, "This is a computer-generated report.")

    c.save()

    return send_file(filepath, as_attachment=True, download_name=filename)


@bp.route("/invoice/<int:invoice_id>/pdf")
@login_required
def invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except ImportError:
        flash("PDF library not installed.", "danger")
        return redirect(url_for("billing.view", invoice_id=invoice_id))

    filename = f"Invoice_{invoice.invoice_number}.pdf"
    filepath = os.path.join(Config.REPORTS_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, Config.APP_NAME)
    y -= 8 * mm
    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, y, f"Invoice #{invoice.invoice_number}")
    y -= 10 * mm

    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Patient: {invoice.patient.full_name}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Date: {invoice.issued_date.strftime('%Y-%m-%d')}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Status: {invoice.status}")
    y -= 12 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Description")
    c.drawString(150 * mm, y, "Amount")
    y -= 3 * mm
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    if invoice.lab_order:
        for ot in invoice.lab_order.tests.all():
            c.drawString(20 * mm, y, ot.test.name)
            c.drawRightString(180 * mm, y, f"{ot.price_at_order:.2f}")
            y -= 6 * mm

    y -= 4 * mm
    c.line(120 * mm, y, width - 20 * mm, y)
    y -= 8 * mm

    c.setFont("Helvetica", 10)
    c.drawString(120 * mm, y, "Subtotal:")
    c.drawRightString(180 * mm, y, f"{invoice.subtotal:.2f}")
    y -= 6 * mm
    c.drawString(120 * mm, y, "Discount:")
    c.drawRightString(180 * mm, y, f"{invoice.discount:.2f}")
    y -= 6 * mm
    c.drawString(120 * mm, y, "Tax:")
    c.drawRightString(180 * mm, y, f"{invoice.tax:.2f}")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(120 * mm, y, "Total:")
    c.drawRightString(180 * mm, y, f"{invoice.total:.2f}")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(120 * mm, y, "Paid:")
    c.drawRightString(180 * mm, y, f"{invoice.amount_paid:.2f}")
    y -= 6 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120 * mm, y, "Balance Due:")
    c.drawRightString(180 * mm, y, f"{invoice.balance_due:.2f}")

    c.save()
    return send_file(filepath, as_attachment=True, download_name=filename)
