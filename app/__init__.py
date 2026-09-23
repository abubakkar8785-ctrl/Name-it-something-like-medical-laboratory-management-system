import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, redirect, url_for, render_template, flash, abort
from flask_login import LoginManager, current_user

from .config import Config
from .models import db, User


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access the system."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    _setup_logging(app, config_class)

    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dashboard_bp
    from .routes.patients import bp as patients_bp
    from .routes.doctors import bp as doctors_bp
    from .routes.lab_orders import bp as lab_orders_bp
    from .routes.samples import bp as samples_bp
    from .routes.results import bp as results_bp
    from .routes.reports import bp as reports_bp
    from .routes.billing import bp as billing_bp
    from .routes.inventory import bp as inventory_bp
    from .routes.settings import bp as settings_bp
    from .routes.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(doctors_bp, url_prefix="/doctors")
    app.register_blueprint(lab_orders_bp, url_prefix="/orders")
    app.register_blueprint(samples_bp, url_prefix="/samples")
    app.register_blueprint(results_bp, url_prefix="/results")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(billing_bp, url_prefix="/billing")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        db.create_all()
        _ensure_default_admin()
        from .seed import seed_test_catalog
        seed_test_catalog()

    @app.context_processor
    def inject_globals():
        return {"app_name": config_class.APP_NAME}

    _register_license_gate(app)
    _register_origin_guard(app)

    return app


# Endpoints reachable with no license activated yet: signing in/out,
# static assets, the desktop launcher's readiness ping, and the license
# activation page itself (otherwise an admin could never reach it to
# fix the problem).
LICENSE_EXEMPT_ENDPOINTS = {
    "auth.login", "auth.logout", "static", "api.health", "settings.license_page",
}


def _register_license_gate(app):
    """
    Enforces Part 90's offline license requirement: every page beyond
    login and the license-activation screen itself is blocked until a
    valid license is on file. Admins are bounced to the activation
    page; everyone else sees a plain "contact your administrator" page
    rather than a confusing redirect they have no permission to follow.
    """
    from .license_check import is_license_valid

    @app.before_request
    def _enforce_license():
        if not current_user.is_authenticated:
            return None
        if request.endpoint is None or request.endpoint in LICENSE_EXEMPT_ENDPOINTS:
            return None
        if is_license_valid():
            return None
        if current_user.is_admin():
            flash("Activate a license to continue using the system.", "warning")
            return redirect(url_for("settings.license_page"))
        return render_template("license_blocked.html"), 403


def _register_origin_guard(app):
    """
    Blocks cross-origin state-changing requests.

    This app is still a real HTTP server bound to 127.0.0.1, even
    though it's shown inside a dedicated desktop window rather than a
    normal browser tab. That means any other webpage open in the
    user's regular browser at the same time could silently POST here
    ("localhost CSRF") — e.g. an attacker page could submit a form to
    http://127.0.0.1:<port>/patients/<id>/delete and the browser would
    send it with no visible sign anything happened, since the local
    server has no same-origin browser tab to compare against on its
    own.

    The desktop window itself never has a reason to send an Origin or
    Referer pointing anywhere but this app's own origin, so any
    request that does is rejected. Requests with neither header set
    (which is what pywebview's same-origin form posts and fetches
    normally look like) are allowed through — this isn't a substitute
    for per-form CSRF tokens against another logged-in instance of the
    app itself, but it stops the realistic threat here: some other
    site reaching across into the local server.
    """
    UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    @app.before_request
    def _block_cross_origin_writes():
        if request.method not in UNSAFE_METHODS:
            return None

        allowed_origin = f"{request.scheme}://{request.host}"

        origin = request.headers.get("Origin")
        if origin is not None and origin != allowed_origin:
            abort(403)

        referer = request.headers.get("Referer")
        if referer is not None and not referer.startswith(allowed_origin + "/") \
                and referer != allowed_origin + "/":
            abort(403)

        return None


def _setup_logging(app, config_class):
    log_path = os.path.join(config_class.LOG_DIR, "app.log")
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Silence Flask's dev-server request logging so no console noise
    # leaks through even if a console were visible.
    werkzeug_log = logging.getLogger("werkzeug")
    werkzeug_log.setLevel(logging.ERROR)


def _ensure_default_admin():
    """Create a first-run default admin account if none exists yet."""
    if User.query.count() == 0:
        admin = User(
            username="admin",
            full_name="System Administrator",
            role="admin",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
