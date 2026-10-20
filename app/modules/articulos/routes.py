from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.decorators import catalog_required
from app.core.errors import DomainError
from app.core.extensions import db
from app.core.forms import (
    form_bool,
    form_decimal,
    form_int,
    form_required,
    form_str,
)
from app.modules.articulos import services
from app.modules.articulos.models import Articulo
from app.modules.categorias.models import Categoria

bp = Blueprint("articulos", __name__, url_prefix="/articulos")


def _categorias():
    return Categoria.query.order_by(Categoria.nombre).all()


def _datos_formulario() -> dict:
    return {
        "codigo": form_required("codigo", "código"),
        "nombre": form_required("nombre", "nombre"),
        "descripcion": form_str("descripcion") or None,
        "unidad_medida": form_required("unidad_medida", "unidad de medida"),
        "categoria_id": form_int("categoria_id", "categoría"),
        "peso_kg": form_decimal("peso_kg", "peso"),
        "precio_unitario": form_decimal("precio_unitario", "precio unitario"),
        "stock_minimo": form_int("stock_minimo", "stock mínimo", default=0, min_value=0),
        "activo": form_bool("activo"),
    }


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    categoria_id = request.args.get("categoria_id", type=int)
    pagination = services.listar(query, categoria_id).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "articulos/list.html",
        pagination=pagination,
        query=query,
        categoria_id=categoria_id,
        categorias=_categorias(),
    )


@bp.route("/crear", methods=["GET", "POST"])
@login_required
@catalog_required
def crear():
    if request.method == "POST":
        try:
            services.crear(_datos_formulario())
            flash("Artículo creado correctamente", "success")
            return redirect(url_for("articulos.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("articulos/form.html", articulo=None, categorias=_categorias())


@bp.route("/<int:articulo_id>/editar", methods=["GET", "POST"])
@login_required
@catalog_required
def editar(articulo_id):
    articulo = db.get_or_404(Articulo, articulo_id)
    if request.method == "POST":
        try:
            services.actualizar(articulo, _datos_formulario())
            flash("Artículo actualizado", "success")
            return redirect(url_for("articulos.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template(
        "articulos/form.html", articulo=articulo, categorias=_categorias()
    )


@bp.post("/<int:articulo_id>/eliminar")
@login_required
@catalog_required
def eliminar(articulo_id):
    articulo = db.get_or_404(Articulo, articulo_id)
    try:
        services.eliminar(articulo)
        flash("Artículo eliminado", "success")
    except DomainError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("articulos.index"))
