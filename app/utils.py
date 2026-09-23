import random
import string
from datetime import datetime

from flask import request
from flask_login import current_user

from .models import db
from .models.audit import AuditLog


def generate_code(prefix, model, field, digits=6):
    """Generate a unique sequential-ish code like PT-000001."""
    while True:
        num = "".join(random.choices(string.digits, k=digits))
        code = f"{prefix}-{num}"
        exists = model.query.filter(getattr(model, field) == code).first()
        if not exists:
            return code


def log_action(action, entity_type, entity_id=None, details=None):
    try:
        entry = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            timestamp=datetime.utcnow(),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()


def parse_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
