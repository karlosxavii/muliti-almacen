from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.core.errors import DomainError
from app.core.extensions import db, login_manager
from app.core.forms import form_bool, form_required, form_str
from app.modules.usuarios import services
from app.modules.usuarios.models import RolUsuario, Usuario

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.before_request
def proteger():
    if not current_user.is_authenticated:
        return login_manager.unauthorized()
    if not current_user.can_manage_users:
        abort(403)


def _leer_rol() -> RolUsuario:
    raw = (request.form.get("rol") or "").strip()
    try:
        return RolUsuario(raw)
    except ValueError:
        raise DomainError("Selecciona un rol válido")


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    pagination = services.listar(query).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "usuarios/list.html", pagination=pagination, query=query, roles=RolUsuario.choices()
    )


@bp.route("/crear", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        try:
            services.crear(
                username=form_required("username", "usuario"),
                nombre_completo=form_required("nombre_completo", "nombre completo"),
                password=form_required("password", "contraseña"),
                rol=_leer_rol(),
                activo=form_bool("activo"),
            )
            flash("Usuario creado correctamente", "success")
            return redirect(url_for("usuarios.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("usuarios/form.html", usuario=None, roles=RolUsuario.choices())


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
def editar(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if request.method == "POST":
        try:
            services.actualizar(
                usuario,
                username=form_required("username", "usuario"),
                nombre_completo=form_required("nombre_completo", "nombre completo"),
                rol=_leer_rol(),
                activo=form_bool("activo"),
                password=form_str("password") or None,
                current_user_id=current_user.id,
            )
            flash("Usuario actualizado", "success")
            return redirect(url_for("usuarios.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template(
        "usuarios/form.html", usuario=usuario, roles=RolUsuario.choices()
    )


@bp.post("/<int:usuario_id>/estado")
def cambiar_estado(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    try:
        services.cambiar_estado(usuario, current_user.id)
        flash("Estado del usuario actualizado", "success")
    except DomainError as exc:
        flash(str(exc), "warning")
    return redirect(url_for("usuarios.index"))
