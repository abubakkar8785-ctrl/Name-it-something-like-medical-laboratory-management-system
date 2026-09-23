from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required

from ..models import Patient, LabOrder, Invoice, InventoryItem, Sample

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    stats = {
        "total_patients": Patient.query.count(),
        "orders_today": LabOrder.query.count(),
        "pending_orders": LabOrder.query.filter(
            LabOrder.status.in_(["Pending", "Sample Collected", "In Progress"])
        ).count(),
        "completed_orders": LabOrder.query.filter_by(status="Completed").count(),
        "pending_samples": Sample.query.filter(
            Sample.status.in_(["Pending Collection", "Collected"])
        ).count(),
        "unpaid_invoices": Invoice.query.filter(
            Invoice.status.in_(["Unpaid", "Partially Paid"])
        ).count(),
        "low_stock_items": sum(
            1 for i in InventoryItem.query.filter_by(active=True).all() if i.low_stock
        ),
    }

    revenue_total = sum(
        inv.amount_paid for inv in Invoice.query.all()
    )
    stats["revenue_total"] = round(revenue_total, 2)

    recent_orders = LabOrder.query.order_by(LabOrder.order_date.desc()).limit(8).all()

    return render_template("dashboard/index.html", stats=stats, recent_orders=recent_orders)
