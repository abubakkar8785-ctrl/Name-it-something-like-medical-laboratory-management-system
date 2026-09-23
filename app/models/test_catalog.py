from datetime import datetime
from . import db


class TestCatalog(db.Model):
    """Master catalog of tests the lab offers (CBC, Lipid Profile, etc.)"""
    __tablename__ = "test_catalog"

    id = db.Column(db.Integer, primary_key=True)
    test_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64))  # Hematology, Biochemistry, Microbiology, etc.
    sample_type = db.Column(db.String(64))  # Blood, Urine, Stool, Swab...
    unit = db.Column(db.String(32))
    reference_range = db.Column(db.String(128))
    price = db.Column(db.Float, default=0.0)
    turnaround_hours = db.Column(db.Integer, default=24)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TestCatalog {self.test_code} {self.name}>"
