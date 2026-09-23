"""
Simple offline license activation.

This is intentionally lightweight: a license "key" is a signed token
that can be validated entirely offline (no internet / phone-home
required), satisfying Part 90 (offline operation) and Part 82
(license/setup screen on startup).

For real commercial use you'd want a stronger scheme (asymmetric
signatures, hardware fingerprint binding, etc.) — this gives you a
working skeleton you can harden later.
"""

import json
import os
import hashlib
import hmac
from datetime import datetime, timedelta

from .config import Config

# In production, keep this secret out of source control (env var,
# or injected at build time). Changing it invalidates all existing keys.
LICENSE_SECRET = os.environ.get("MEDLAB_LICENSE_SECRET", "change-this-license-signing-secret")


def _sign(payload: str) -> str:
    return hmac.new(LICENSE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def generate_license_key(customer_name: str, days_valid: int = 3650) -> str:
    """
    Utility for the vendor (you) to generate a license key to hand to a
    customer. Not exposed in the UI — run manually, e.g.:

        python -c "from app.license_check import generate_license_key as g; print(g('Acme Labs'))"
    """
    expiry = (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
    payload = f"{customer_name}|{expiry}"
    signature = _sign(payload)
    raw = f"{payload}|{signature}"
    return raw.encode().hex()


def _decode(key: str):
    try:
        raw = bytes.fromhex(key).decode()
        customer_name, expiry, signature = raw.split("|")
        payload = f"{customer_name}|{expiry}"
        if not hmac.compare_digest(_sign(payload), signature):
            return None
        return {"customer_name": customer_name, "expiry": expiry}
    except Exception:
        return None


def activate_license(key: str):
    info = _decode(key)
    if not info:
        return False, "Invalid license key."

    expiry_date = datetime.strptime(info["expiry"], "%Y-%m-%d").date()
    if expiry_date < datetime.utcnow().date():
        return False, "This license key has expired."

    with open(Config.LICENSE_FILE, "w") as f:
        json.dump({
            "key": key,
            "customer_name": info["customer_name"],
            "expiry": info["expiry"],
            "activated_at": datetime.utcnow().isoformat(),
        }, f, indent=2)

    return True, f"License activated for {info['customer_name']} (valid until {info['expiry']})."


def read_license():
    if not os.path.isfile(Config.LICENSE_FILE):
        return None
    try:
        with open(Config.LICENSE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def is_license_valid():
    info = read_license()
    if not info:
        return False
    try:
        expiry_date = datetime.strptime(info["expiry"], "%Y-%m-%d").date()
        return expiry_date >= datetime.utcnow().date()
    except Exception:
        return False
