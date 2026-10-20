from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.movimientos.models import Movimiento, MovimientoDetalle, TipoMovimiento
from app.modules.stock import services as stock_service


class MovimientoError(DomainError):
    pass


def listar(
    query: str | None = None,
    tipo: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
):
    stmt = Movimiento.query.options(
        joinedload(Movimiento.usuario),
        selectinload(Movimiento.detalles).joinedload(MovimientoDetalle.lote),
    )
    if tipo in {TipoMovimiento.ENTRADA.value, TipoMovimiento.SALIDA.value}:
        stmt = stmt.filter(Movimiento.tipo == TipoMovimiento(tipo))
    if desde:
        stmt = stmt.filter(Movimiento.fecha_movimiento >= datetime.combine(desde, time.min))
    if hasta:
        stmt = stmt.filter(Movimiento.fecha_movimiento <= datetime.combine(hasta, time.max))
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(func.coalesce(Movimiento.documento, "")).like(term)
            | func.lower(func.coalesce(Movimiento.observacion, "")).like(term)
        )
    return stmt.order_by(Movimiento.fecha_movimiento.desc(), Movimiento.id.desc())


def obtener(movimiento_id: int):
    return (
        Movimiento.query.options(
            joinedload(Movimiento.usuario),
            selectinload(Movimiento.detalles).joinedload(MovimientoDetalle.lote),
            selectinload(Movimiento.detalles).joinedload(MovimientoDetalle.estante_origen),
            selectinload(Movimiento.detalles).joinedload(MovimientoDetalle.estante_destino),
        )
        .filter_by(id=movimiento_id)
        .first()
    )


def _to_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise MovimientoError("El precio unitario no es válido")


def _to_int(value, label="cantidad"):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise MovimientoError(f"La {label} no es válida")
    return number


def normalizar_detalles(tipo: TipoMovimiento, detalles: list[dict]) -> list[dict]:
    if not detalles:
        raise MovimientoError("El movimiento debe tener al menos una línea")

    normalized = []
    solicitado_por_lote = defaultdict(int)
    solicitado_por_estante = defaultdict(int)

    for index, item in enumerate(detalles, start=1):
        lote_id = _to_int(item.get("lote_id"), f"lote de la línea {index}")
        cantidad = _to_int(item.get("cantidad"), f"cantidad de la línea {index}")
        if cantidad <= 0:
            raise MovimientoError(f"La cantidad de la línea {index} debe ser mayor que cero")

        lote = db.session.get(Lote, lote_id)
        if not lote:
            raise MovimientoError(f"El lote de la línea {index} no existe")

        origen_id = _to_int(item.get("estante_origen_id"), "estante de origen") if item.get("estante_origen_id") else None
        destino_id = _to_int(item.get("estante_destino_id"), "estante de destino") if item.get("estante_destino_id") else None

        if tipo == TipoMovimiento.ENTRADA:
            if not destino_id:
                raise MovimientoError(f"La línea {index} necesita un estante de destino")
            if origen_id:
                raise MovimientoError(f"La línea {index} de entrada no puede tener estante de origen")
        else:
            if not origen_id:
                raise MovimientoError(f"La línea {index} necesita un estante de origen")
            if destino_id and destino_id == origen_id:
                raise MovimientoError(f"La línea {index} no puede tener el mismo origen y destino")

        if origen_id and not db.session.get(Estante, origen_id):
            raise MovimientoError(f"El estante de origen de la línea {index} no existe")
        if destino_id and not db.session.get(Estante, destino_id):
            raise MovimientoError(f"El estante de destino de la línea {index} no existe")

        if tipo == TipoMovimiento.SALIDA:
            solicitado_por_lote[lote_id] += cantidad
            solicitado_por_estante[(lote_id, origen_id)] += cantidad

        normalized.append(
            {
                "lote_id": lote_id,
                "cantidad": cantidad,
                "estante_origen_id": origen_id,
                "estante_destino_id": destino_id,
                "precio_unitario": _to_decimal(item.get("precio_unitario")),
                "observacion": (item.get("observacion") or "").strip() or None,
            }
        )

    if tipo == TipoMovimiento.SALIDA:
        for lote_id, cantidad in solicitado_por_lote.items():
            disponible = stock_service.stock_lote(lote_id)
            if cantidad > disponible:
                lote = db.session.get(Lote, lote_id)
                raise MovimientoError(
                    f"Stock insuficiente para el lote {lote.numero_lote}. "
                    f"Disponible: {disponible}, solicitado: {cantidad}"
                )
        for (lote_id, estante_id), cantidad in solicitado_por_estante.items():
            disponible = stock_service.stock_lote_estante(lote_id, estante_id)
            if cantidad > disponible:
                lote = db.session.get(Lote, lote_id)
                estante = db.session.get(Estante, estante_id)
                raise MovimientoError(
                    f"Stock insuficiente en {estante.nombre_completo} para el lote "
                    f"{lote.numero_lote}. Disponible: {disponible}, solicitado: {cantidad}"
                )

    return normalized


def registrar_movimiento(
    tipo,
    usuario_id,
    detalles: list[dict],
    documento: str | None = None,
    observacion: str | None = None,
    fecha_movimiento: datetime | None = None,
) -> Movimiento:
    try:
        tipo_enum = tipo if isinstance(tipo, TipoMovimiento) else TipoMovimiento(str(tipo).upper())
    except ValueError:
        raise MovimientoError("El tipo de movimiento no es válido")

    normalized = normalizar_detalles(tipo_enum, detalles)

    movimiento = Movimiento(
        tipo=tipo_enum,
        documento=(documento or "").strip() or None,
        observacion=(observacion or "").strip() or None,
        usuario_id=usuario_id,
        fecha_movimiento=fecha_movimiento or datetime.now(),
    )
    db.session.add(movimiento)
    db.session.flush()

    for item in normalized:
        db.session.add(MovimientoDetalle(movimiento_id=movimiento.id, **item))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return movimiento
