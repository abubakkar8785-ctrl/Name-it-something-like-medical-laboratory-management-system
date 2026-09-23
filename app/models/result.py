from datetime import datetime
from . import db


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    lab_order_test_id = db.Column(db.Integer, db.ForeignKey("lab_order_tests.id"),
                                   unique=True, nullable=False)

    value = db.Column(db.String(128))
    unit = db.Column(db.String(32))
    reference_range = db.Column(db.String(128))
    flag = db.Column(db.String(16))  # Normal, High, Low, Critical

    notes = db.Column(db.Text)

    performed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    performed_at = db.Column(db.DateTime)
    verified_at = db.Column(db.DateTime)

    status = db.Column(db.String(32), default="Pending")
    # statuses: Pending, Entered, Verified, Amended

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Result {self.id} flag={self.flag}>"
