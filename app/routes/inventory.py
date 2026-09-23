from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ..models import db, InventoryItem, InventoryTransaction
from ..utils import generate_code, log_action, parse_date

bp = Blueprint("inventory", __name__)


@bp.route("/")
@login_required
def index():
    items = InventoryItem.query.filter_by(active=True).order_by(InventoryItem.name).all()
    return render_template("inventory/index.html", items=items)


@bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        item = InventoryItem(
            item_code=generate_code("INV-ITM", InventoryItem, "item_code"),
            name=request.form["name"].strip(),
            category=request.form.get("category"),
            unit=request.form.get("unit"),
            quantity_on_hand=float(request.form.get("quantity_on_hand") or 0),
            reorder_level=float(request.form.get("reorder_level") or 0),
            unit_cost=float(request.form.get("unit_cost") or 0),
            supplier=request.form.get("supplier"),
            expiry_date=parse_date(request.form.get("expiry_date")),
            location=request.form.get("location"),
        )
        db.session.add(item)
        db.session.commit()
        log_action("CREATE", "InventoryItem", item.id, item.name)
        flash(f"Item {item.name} added to inventory.", "success")
        return redirect(url_for("inventory.index"))
    return render_template("inventory/form.html", item=None)


@bp.route("/<int:item_id>/adjust", methods=["POST"])
@login_required
def adjust(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    qty = float(request.form.get("quantity") or 0)
    ttype = request.form.get("transaction_type", "IN")
    reason = request.form.get("reason", "")

    if ttype == "IN":
        item.quantity_on_hand += qty
    elif ttype == "OUT":
        item.quantity_on_hand = max(item.quantity_on_hand - qty, 0)
    else:
        item.quantity_on_hand = qty  # ADJUSTMENT sets absolute value

    txn = InventoryTransaction(
        item_id=item.id,
        transaction_type=ttype,
        quantity=qty,
        reason=reason,
        performed_by_id=current_user.id,
    )
    db.session.add(txn)
    db.session.commit()
    log_action("UPDATE", "InventoryItem", item.id, f"{ttype} {qty}")
    flash(f"Inventory updated for {item.name}.", "success")
    return redirect(url_for("inventory.index"))
