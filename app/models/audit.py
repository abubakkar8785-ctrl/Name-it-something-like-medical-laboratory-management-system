from datetime import datetime
from . import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(64))  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT...
    entity_type = db.Column(db.String(64))  # Patient, LabOrder, Result...
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
