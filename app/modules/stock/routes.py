from flask import Blueprint, render_template, request
from flask_login import login_required

from app.modules.stock import services

bp = Blueprint("stock", __name__, url_prefix="/stock")


@bp.route("/lotes")
@login_required
def lotes():
    query = (request.args.get("q") or "").strip()
    solo = request.args.get("solo") == "1"
    items = services.listar_stock_lotes(query=query, solo_con_stock=solo)
    return render_template("stock/lotes.html", items=items, query=query, solo=solo)


@bp.route("/articulos")
@login_required
def articulos():
    query = (request.args.get("q") or "").strip()
    solo = request.args.get("bajo") == "1"
    items = services.listar_stock_articulos(query=query, solo_bajo_stock=solo)
    return render_template("stock/articulos.html", items=items, query=query, solo=solo)


@bp.route("/almacenes")
@login_required
def almacenes():
    items = services.listar_stock_almacenes()
    return render_template("stock/almacenes.html", items=items)
