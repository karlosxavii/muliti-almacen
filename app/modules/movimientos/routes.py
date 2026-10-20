from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.core.errors import DomainError
from app.core.forms import FormError, form_date, form_str
from app.modules.articulos.models import Articulo
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.movimientos import services
from app.modules.movimientos.models import TipoMovimiento

bp = Blueprint("movimientos", __name__, url_prefix="/movimientos")


def _parse_fecha(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _referencias():
    lotes = (
        Lote.query.join(Articulo)
        .options(joinedload(Lote.articulo))
        .order_by(Articulo.nombre, Lote.numero_lote)
        .all()
    )
    estantes = (
        Estante.query.join(Estante.almacen)
        .options(joinedload(Estante.almacen))
        .order_by(Estante.almacen_id, Estante.codigo)
        .all()
    )
    return lotes, estantes


@bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    tipo = (request.args.get("tipo") or "").strip().upper()
    query = (request.args.get("q") or "").strip()
    desde = _parse_fecha(request.args.get("desde"))
    hasta = _parse_fecha(request.args.get("hasta"))

    pagination = services.listar(query, tipo, desde, hasta).paginate(
        page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False
    )
    return render_template(
        "movimientos/list.html",
        pagination=pagination,
        tipo=tipo,
        query=query,
        desde=request.args.get("desde", ""),
        hasta=request.args.get("hasta", ""),
        TipoMovimiento=TipoMovimiento,
    )


@bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar():
    lotes, estantes = _referencias()

    if request.method == "POST":
        try:
            tipo = (request.form.get("tipo") or "").strip().upper()
            if tipo not in {TipoMovimiento.ENTRADA.value, TipoMovimiento.SALIDA.value}:
                raise FormError("Selecciona un tipo de movimiento válido")

            lote_values = request.form.getlist("detalle_lote")
            cantidades = request.form.getlist("detalle_cantidad")
            origenes = request.form.getlist("detalle_origen")
            destinos = request.form.getlist("detalle_destino")
            precios = request.form.getlist("detalle_precio")

            detalles = []
            for index in range(len(lote_values)):
                lote_id = lote_values[index].strip()
                cantidad = cantidades[index].strip() if index < len(cantidades) else ""
                if not lote_id and not cantidad:
                    continue
                if not lote_id:
                    raise FormError(f"Selecciona un lote en la línea {index + 1}")
                if not cantidad:
                    raise FormError(f"Indica la cantidad en la línea {index + 1}")
                detalles.append(
                    {
                        "lote_id": lote_id,
                        "cantidad": cantidad,
                        "estante_origen_id": origenes[index] if index < len(origenes) else "",
                        "estante_destino_id": destinos[index] if index < len(destinos) else "",
                        "precio_unitario": precios[index] if index < len(precios) else "",
                    }
                )

            if not detalles:
                raise FormError("Agrega al menos una línea al movimiento")

            fecha = form_date("fecha_movimiento", "fecha del movimiento")
            fecha_movimiento = (
                datetime.combine(fecha, datetime.now().time()) if fecha else None
            )

            movimiento = services.registrar_movimiento(
                tipo=tipo,
                usuario_id=current_user.id,
                detalles=detalles,
                documento=form_str("documento"),
                observacion=form_str("observacion"),
                fecha_movimiento=fecha_movimiento,
            )
            flash("Movimiento registrado correctamente", "success")
            return redirect(url_for("movimientos.detalle", movimiento_id=movimiento.id))
        except DomainError as exc:
            flash(str(exc), "danger")

    return render_template(
        "movimientos/form.html",
        lotes=lotes,
        estantes=estantes,
        TipoMovimiento=TipoMovimiento,
        hoy=datetime.now().strftime("%Y-%m-%d"),
    )


@bp.route("/<int:movimiento_id>")
@login_required
def detalle(movimiento_id):
    movimiento = services.obtener(movimiento_id)
    if not movimiento:
        abort(404)
    return render_template("movimientos/detail.html", movimiento=movimiento)
