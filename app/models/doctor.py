from datetime import datetime
from . import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    doctor_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    specialty = db.Column(db.String(128))
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    clinic_hospital = db.Column(db.String(128))
    commission_percent = db.Column(db.Float, default=0.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patients = db.relationship("Patient", backref="referring_doctor", lazy="dynamic")
    lab_orders = db.relationship("LabOrder", backref="ordering_doctor", lazy="dynamic")

    def __repr__(self):
        return f"<Doctor {self.doctor_code} {self.full_name}>"
