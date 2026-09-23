from datetime import datetime
from . import db


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    lab_order_id = db.Column(db.Integer, db.ForeignKey("lab_orders.id"))

    subtotal = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    amount_paid = db.Column(db.Float, default=0.0)

    status = db.Column(db.String(32), default="Unpaid")
    # statuses: Unpaid, Partially Paid, Paid, Cancelled, Refunded

    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", backref="invoice", lazy="dynamic",
                                cascade="all, delete-orphan")

    @property
    def balance_due(self):
        return round(self.total - self.amount_paid, 2)

    def __repr__(self):
        return f"<Invoice {self.invoice_number} {self.status}>"


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)

    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(32), default="Cash")  # Cash, Card, Bank Transfer, Insurance
    reference = db.Column(db.String(64))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return f"<Payment {self.amount} for invoice {self.invoice_id}>"
