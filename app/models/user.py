from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="staff")
    # roles: admin, lab_technician, receptionist, doctor, accountant, staff
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
