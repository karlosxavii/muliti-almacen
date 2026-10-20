from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.decorators import catalog_required
from app.core.errors import DomainError
from app.core.extensions import db
from app.core.forms import form_int, form_required, form_str
from app.modules.almacenes.models import Almacen
from app.modules.estantes import services
from app.modules.estantes.models import Estante

bp = Blueprint("estantes", __name__, url_prefix="/estantes")


def _almacenes():
    return Almacen.query.order_by(Almacen.nombre).all()


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    almacen_id = request.args.get("almacen_id", type=int)
    pagination = services.listar(query, almacen_id).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "estantes/list.html",
        pagination=pagination,
        query=query,
        almacen_id=almacen_id,
        almacenes=_almacenes(),
    )


@bp.route("/crear", methods=["GET", "POST"])
@login_required
@catalog_required
def crear():
    if request.method == "POST":
        try:
            services.crear(
                codigo=form_required("codigo", "código"),
                nombre=form_str("nombre"),
                descripcion=form_str("descripcion"),
                almacen_id=form_int("almacen_id", "almacén", required=True),
            )
            flash("Estante creado correctamente", "success")
            return redirect(url_for("estantes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("estantes/form.html", estante=None, almacenes=_almacenes())


@bp.route("/<int:estante_id>/editar", methods=["GET", "POST"])
@login_required
@catalog_required
def editar(estante_id):
    estante = db.get_or_404(Estante, estante_id)
    if request.method == "POST":
        try:
            services.actualizar(
                estante,
                codigo=form_required("codigo", "código"),
                nombre=form_str("nombre"),
                descripcion=form_str("descripcion"),
                almacen_id=form_int("almacen_id", "almacén", required=True),
            )
            flash("Estante actualizado", "success")
            return redirect(url_for("estantes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("estantes/form.html", estante=estante, almacenes=_almacenes())


@bp.post("/<int:estante_id>/eliminar")
@login_required
@catalog_required
def eliminar(estante_id):
    estante = db.get_or_404(Estante, estante_id)
    try:
        services.eliminar(estante)
        flash("Estante eliminado", "success")
    except DomainError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("estantes.index"))
