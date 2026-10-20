from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.decorators import catalog_required
from app.core.errors import DomainError
from app.core.extensions import db
from app.core.forms import form_date, form_int, form_required, form_str
from app.modules.articulos.models import Articulo
from app.modules.estantes.models import Estante
from app.modules.lotes import services
from app.modules.lotes.models import Lote

bp = Blueprint("lotes", __name__, url_prefix="/lotes")


def _referencias():
    articulos = Articulo.query.order_by(Articulo.nombre).all()
    estantes = (
        Estante.query.join(Estante.almacen)
        .order_by(Estante.almacen_id, Estante.codigo)
        .all()
    )
    return articulos, estantes


def _datos_formulario() -> dict:
    return {
        "numero_lote": form_required("numero_lote", "número de lote"),
        "articulo_id": form_int("articulo_id", "artículo", required=True),
        "fecha_fabricacion": form_date("fecha_fabricacion", "fecha de fabricación"),
        "fecha_vencimiento": form_date("fecha_vencimiento", "fecha de vencimiento"),
        "proveedor": form_str("proveedor") or None,
        "estante_id": form_int("estante_id", "estante"),
        "cantidad_inicial": form_int(
            "cantidad_inicial", "cantidad inicial", default=0, min_value=0
        ),
    }


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    articulo_id = request.args.get("articulo_id", type=int)
    pagination = services.listar(query, articulo_id).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "lotes/list.html",
        pagination=pagination,
        query=query,
        articulo_id=articulo_id,
        articulos=Articulo.query.order_by(Articulo.nombre).all(),
    )


@bp.route("/crear", methods=["GET", "POST"])
@login_required
@catalog_required
def crear():
    articulos, estantes = _referencias()
    if request.method == "POST":
        try:
            services.crear(_datos_formulario())
            flash("Lote creado correctamente", "success")
            return redirect(url_for("lotes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template(
        "lotes/form.html", lote=None, articulos=articulos, estantes=estantes
    )


@bp.route("/<int:lote_id>/editar", methods=["GET", "POST"])
@login_required
@catalog_required
def editar(lote_id):
    lote = db.get_or_404(Lote, lote_id)
    articulos, estantes = _referencias()
    if request.method == "POST":
        try:
            services.actualizar(lote, _datos_formulario())
            flash("Lote actualizado", "success")
            return redirect(url_for("lotes.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template(
        "lotes/form.html", lote=lote, articulos=articulos, estantes=estantes
    )


@bp.post("/<int:lote_id>/eliminar")
@login_required
@catalog_required
def eliminar(lote_id):
    lote = db.get_or_404(Lote, lote_id)
    try:
        services.eliminar(lote)
        flash("Lote eliminado", "success")
    except DomainError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("lotes.index"))
