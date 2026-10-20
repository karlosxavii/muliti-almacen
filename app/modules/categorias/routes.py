from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.decorators import catalog_required
from app.core.errors import DomainError
from app.core.extensions import db
from app.core.forms import form_required, form_str
from app.modules.categorias import services
from app.modules.categorias.models import Categoria

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    query = (request.args.get("q") or "").strip()
    pagination = services.listar(query).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template("categorias/list.html", pagination=pagination, query=query)


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
            flash("Categoría creada correctamente", "success")
            return redirect(url_for("categorias.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("categorias/form.html", categoria=None)


@bp.route("/<int:categoria_id>/editar", methods=["GET", "POST"])
@login_required
@catalog_required
def editar(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)
    if request.method == "POST":
        try:
            services.actualizar(
                categoria,
                codigo=form_required("codigo", "código"),
                nombre=form_required("nombre", "nombre"),
                descripcion=form_str("descripcion"),
            )
            flash("Categoría actualizada", "success")
            return redirect(url_for("categorias.index"))
        except DomainError as exc:
            flash(str(exc), "danger")
    return render_template("categorias/form.html", categoria=categoria)


@bp.post("/<int:categoria_id>/eliminar")
@login_required
@catalog_required
def eliminar(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)
    try:
        services.eliminar(categoria)
        flash("Categoría eliminada", "success")
    except DomainError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("categorias.index"))
