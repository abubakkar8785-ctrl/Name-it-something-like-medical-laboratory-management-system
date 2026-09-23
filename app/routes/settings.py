import os
import json
import shutil
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user

from ..models import db, TestCatalog, User
from ..utils import generate_code, log_action
from ..config import Config

bp = Blueprint("settings", __name__)


def admin_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Administrator access required.", "danger")
            return redirect(url_for("dashboard.index"))
        return view(*args, **kwargs)

    return wrapped


@bp.route("/")
@login_required
def index():
    return render_template("settings/index.html")


# ---------- Test Catalog ----------

@bp.route("/tests")
@login_required
def tests():
    catalog = TestCatalog.query.order_by(TestCatalog.category, TestCatalog.name).all()
    return render_template("settings/tests.html", catalog=catalog)


@bp.route("/tests/new", methods=["GET", "POST"])
@login_required
def new_test():
    if request.method == "POST":
        t = TestCatalog(
            test_code=generate_code("TST", TestCatalog, "test_code", digits=4),
            name=request.form["name"].strip(),
            category=request.form.get("category"),
            sample_type=request.form.get("sample_type"),
            unit=request.form.get("unit"),
            reference_range=request.form.get("reference_range"),
            price=float(request.form.get("price") or 0),
            turnaround_hours=int(request.form.get("turnaround_hours") or 24),
        )
        db.session.add(t)
        db.session.commit()
        log_action("CREATE", "TestCatalog", t.id, t.name)
        flash(f"Test '{t.name}' added to catalog.", "success")
        return redirect(url_for("settings.tests"))
    return render_template("settings/test_form.html", test=None)


@bp.route("/tests/<int:test_id>/edit", methods=["GET", "POST"])
@login_required
def edit_test(test_id):
    t = TestCatalog.query.get_or_404(test_id)
    if request.method == "POST":
        t.name = request.form["name"].strip()
        t.category = request.form.get("category")
        t.sample_type = request.form.get("sample_type")
        t.unit = request.form.get("unit")
        t.reference_range = request.form.get("reference_range")
        t.price = float(request.form.get("price") or 0)
        t.turnaround_hours = int(request.form.get("turnaround_hours") or 24)
        t.active = bool(request.form.get("active"))
        db.session.commit()
        log_action("UPDATE", "TestCatalog", t.id, t.name)
        flash("Test catalog entry updated.", "success")
        return redirect(url_for("settings.tests"))
    return render_template("settings/test_form.html", test=t)


# ---------- Users ----------

@bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.username).all()
    return render_template("settings/users.html", users=all_users)


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    if request.method == "POST":
        u = User(
            username=request.form["username"].strip(),
            full_name=request.form["full_name"].strip(),
            email=request.form.get("email"),
            role=request.form.get("role", "staff"),
        )
        u.set_password(request.form.get("password") or "changeme123")
        db.session.add(u)
        db.session.commit()
        log_action("CREATE", "User", u.id, u.username)
        flash(f"User {u.username} created.", "success")
        return redirect(url_for("settings.users"))
    return render_template("settings/user_form.html", user=None)


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    u = User.query.get_or_404(user_id)
    if request.method == "POST":
        u.full_name = request.form["full_name"].strip()
        u.email = request.form.get("email")
        u.role = request.form.get("role", u.role)
        u.active = bool(request.form.get("active"))
        new_password = request.form.get("password")
        if new_password:
            u.set_password(new_password)
        db.session.commit()
        log_action("UPDATE", "User", u.id, u.username)
        flash("User updated.", "success")
        return redirect(url_for("settings.users"))
    return render_template("settings/user_form.html", user=u)


# ---------- Backup / Restore ----------

@bp.route("/backup")
@login_required
@admin_required
def backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"medlab_backup_{timestamp}.db"
    backup_path = os.path.join(Config.BACKUP_DIR, backup_name)
    shutil.copy2(Config.DB_PATH, backup_path)
    log_action("BACKUP", "Database", None, backup_name)
    flash(f"Backup created: {backup_name}", "success")
    return send_file(backup_path, as_attachment=True, download_name=backup_name)


@bp.route("/backups")
@login_required
@admin_required
def list_backups():
    files = []
    if os.path.isdir(Config.BACKUP_DIR):
        for fn in sorted(os.listdir(Config.BACKUP_DIR), reverse=True):
            full = os.path.join(Config.BACKUP_DIR, fn)
            files.append({
                "name": fn,
                "size_kb": round(os.path.getsize(full) / 1024, 1),
                "modified": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M"),
            })
    return render_template("settings/backups.html", files=files)


@bp.route("/restore/<path:filename>", methods=["POST"])
@login_required
@admin_required
def restore(filename):
    backup_path = os.path.join(Config.BACKUP_DIR, filename)
    if not os.path.isfile(backup_path):
        flash("Backup file not found.", "danger")
        return redirect(url_for("settings.list_backups"))

    # Safety copy of current DB before overwriting
    safety_name = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(Config.DB_PATH, os.path.join(Config.BACKUP_DIR, safety_name))

    db.session.remove()
    db.engine.dispose()
    shutil.copy2(backup_path, Config.DB_PATH)

    log_action("RESTORE", "Database", None, filename)
    flash(f"Database restored from {filename}. Please restart the application.", "success")
    return redirect(url_for("settings.list_backups"))


# ---------- License ----------

@bp.route("/license", methods=["GET", "POST"])
@login_required
@admin_required
def license_page():
    from ..license_check import read_license, activate_license

    current = read_license()

    if request.method == "POST":
        key = request.form.get("license_key", "").strip()
        ok, message = activate_license(key)
        flash(message, "success" if ok else "danger")
        return redirect(url_for("settings.license_page"))

    return render_template("settings/license.html", license_info=current)
