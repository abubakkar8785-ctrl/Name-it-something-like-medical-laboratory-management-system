from datetime import datetime
from . import db


class Sample(db.Model):
    __tablename__ = "samples"

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey("lab_orders.id"), nullable=False)

    sample_type = db.Column(db.String(64))  # Blood, Urine, Stool, Swab...
    collection_datetime = db.Column(db.DateTime)
    collected_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    status = db.Column(db.String(32), default="Pending Collection")
    # statuses: Pending Collection, Collected, Received in Lab,
    #           Rejected, Processed, Disposed

    rejection_reason = db.Column(db.String(256))
    storage_location = db.Column(db.String(64))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Sample {self.sample_id} ({self.status})>"
