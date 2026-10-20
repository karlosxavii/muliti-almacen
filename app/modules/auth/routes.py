from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.modules.auth.services import autenticar, registrar_acceso

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _safe_next(target: str | None) -> bool:
    if not target:
        return False
    host = urlparse(request.host_url)
    candidate = urlparse(urljoin(request.host_url, target))
    return candidate.scheme in {"http", "https"} and host.netloc == candidate.netloc


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = autenticar(username, password)

        if not user:
            flash("Usuario o contraseña incorrectos", "danger")
            return render_template("auth/login.html", username=username), 401

        login_user(user, remember=bool(request.form.get("remember")))
        registrar_acceso(user)

        destination = request.args.get("next")
        if _safe_next(destination):
            return redirect(destination)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html", username="")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for("auth.login"))
