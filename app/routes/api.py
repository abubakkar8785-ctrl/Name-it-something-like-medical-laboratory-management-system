from flask import Blueprint, jsonify

bp = Blueprint("api", __name__)


@bp.route("/health")
def health():
    """Used by the desktop launcher to detect when Flask is ready."""
    return jsonify(status="ok")
