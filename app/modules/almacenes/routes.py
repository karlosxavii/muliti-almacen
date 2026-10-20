from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.decorators import catalog_required
from app.core.errors import DomainError
from app.core.extensions import db
from app.core.forms import form_required, form_str
from app.modules.almacenes import services
from app.modules.almacenes.models import Almacen

bp = Blueprint("almacenes", __name__, url_prefix="/almacenes")


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    pagination = services.listar(query).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("almacenes/list.html", pagination=pagination, query=query)


@bp.route("/crear", methods=["GET", "POST"])
@login_required
@catalog_required
def crear():
    if request.method == "POST":
        try:
            services.crear(
                codigo=form_required("codigo", "código"),
                nombre=form_required("nombre", "nombre"),
                descripcion=form_str("descripcion"),
            )
            flash("Almacén creado correctamente", "success")
            return redirect(url_for("almacenes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("almacenes/form.html", almacen=None)


@bp.route("/<int:almacen_id>/editar", methods=["GET", "POST"])
@login_required
@catalog_required
def editar(almacen_id):
    almacen = db.get_or_404(Almacen, almacen_id)
    if request.method == "POST":
        try:
            services.actualizar(
                almacen,
                codigo=form_required("codigo", "código"),
                nombre=form_required("nombre", "nombre"),
                descripcion=form_str("descripcion"),
            )
            flash("Almacén actualizado", "success")
            return redirect(url_for("almacenes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("almacenes/form.html", almacen=almacen)


@bp.post("/<int:almacen_id>/eliminar")
@login_required
@catalog_required
def eliminar(almacen_id):
    almacen = db.get_or_404(Almacen, almacen_id)
    try:
        services.eliminar(almacen)
        flash("Almacén eliminado", "success")
    except DomainError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("almacenes.index"))
