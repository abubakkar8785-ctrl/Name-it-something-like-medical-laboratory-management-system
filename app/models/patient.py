from datetime import datetime, date
from . import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    patient_code = db.Column(db.String(20), unique=True, nullable=False, index=True)

    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male / Female / Other
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    address = db.Column(db.String(256))
    city = db.Column(db.String(64))

    blood_group = db.Column(db.String(8))
    allergies = db.Column(db.Text)
    medical_notes = db.Column(db.Text)

    emergency_contact_name = db.Column(db.String(128))
    emergency_contact_phone = db.Column(db.String(32))

    referring_doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lab_orders = db.relationship("LabOrder", backref="patient", lazy="dynamic")
    invoices = db.relationship("Invoice", backref="patient", lazy="dynamic")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __repr__(self):
        return f"<Patient {self.patient_code} {self.full_name}>"
