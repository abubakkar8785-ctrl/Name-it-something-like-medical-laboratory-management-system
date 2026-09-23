from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..models import db, User
from ..utils import log_action

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.active and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_action("LOGIN", "User", user.id, f"{user.username} logged in")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    log_action("LOGOUT", "User", current_user.id, f"{current_user.username} logged out")
    logout_user()
    return redirect(url_for("auth.login"))
