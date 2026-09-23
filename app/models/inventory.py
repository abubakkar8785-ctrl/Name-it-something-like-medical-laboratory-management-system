from datetime import datetime
from . import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64))  # Reagent, Consumable, Equipment
    unit = db.Column(db.String(32))  # box, ml, piece...
    quantity_on_hand = db.Column(db.Float, default=0.0)
    reorder_level = db.Column(db.Float, default=0.0)
    unit_cost = db.Column(db.Float, default=0.0)
    supplier = db.Column(db.String(128))
    expiry_date = db.Column(db.Date)
    location = db.Column(db.String(64))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("InventoryTransaction", backref="item", lazy="dynamic")

    @property
    def low_stock(self):
        return self.quantity_on_hand <= self.reorder_level

    def __repr__(self):
        return f"<InventoryItem {self.item_code} {self.name}>"


class InventoryTransaction(db.Model):
    __tablename__ = "inventory_transactions"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id"), nullable=False)
    transaction_type = db.Column(db.String(16))  # IN, OUT, ADJUSTMENT
    quantity = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(256))
    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
