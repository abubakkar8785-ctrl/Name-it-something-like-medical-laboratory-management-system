from datetime import datetime
from . import db


class LabOrder(db.Model):
    __tablename__ = "lab_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"))

    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(16), default="Routine")  # Routine, Urgent, STAT
    status = db.Column(db.String(32), default="Pending")
    # statuses: Pending, Sample Collected, In Progress, Completed, Cancelled, Reported

    clinical_notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tests = db.relationship("LabOrderTest", backref="lab_order", lazy="dynamic",
                             cascade="all, delete-orphan")
    samples = db.relationship("Sample", backref="lab_order", lazy="dynamic")
    invoice = db.relationship("Invoice", backref="lab_order", uselist=False)

    def __repr__(self):
        return f"<LabOrder {self.order_number}>"


class LabOrderTest(db.Model):
    """Join table: which catalog tests were ordered on this lab order."""
    __tablename__ = "lab_order_tests"

    id = db.Column(db.Integer, primary_key=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey("lab_orders.id"), nullable=False)
    test_catalog_id = db.Column(db.Integer, db.ForeignKey("test_catalog.id"), nullable=False)
    price_at_order = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(32), default="Pending")

    test = db.relationship("TestCatalog")
    result = db.relationship("Result", backref="order_test", uselist=False)
