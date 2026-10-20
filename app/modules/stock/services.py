from sqlalchemy import case, func, select

from app.core.extensions import db
from app.modules.almacenes.models import Almacen
from app.modules.articulos.models import Articulo
from app.modules.categorias.models import Categoria
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.movimientos.models import (
    Movimiento,
    MovimientoDetalle,
    TipoMovimiento,
)


def _saldo_expr():
    return case(
        (Movimiento.tipo == TipoMovimiento.ENTRADA, MovimientoDetalle.cantidad),
        else_=-MovimientoDetalle.cantidad,
    )


def _scalar_int(stmt) -> int:
    value = db.session.execute(stmt).scalar()
    return int(value or 0)


def stock_lote(lote_id: int) -> int:
    stmt = (
        select(func.coalesce(func.sum(_saldo_expr()), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .where(MovimientoDetalle.lote_id == lote_id)
    )
    return _scalar_int(stmt)


def stock_lote_estante(lote_id: int, estante_id: int) -> int:
    entradas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .where(
            MovimientoDetalle.lote_id == lote_id,
            MovimientoDetalle.estante_destino_id == estante_id,
            Movimiento.tipo == TipoMovimiento.ENTRADA,
        )
    )
    salidas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .where(
            MovimientoDetalle.lote_id == lote_id,
            MovimientoDetalle.estante_origen_id == estante_id,
            Movimiento.tipo == TipoMovimiento.SALIDA,
        )
    )
    return _scalar_int(entradas) - _scalar_int(salidas)


def stock_estante(estante_id: int) -> int:
    entradas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .where(
            MovimientoDetalle.estante_destino_id == estante_id,
            Movimiento.tipo == TipoMovimiento.ENTRADA,
        )
    )
    salidas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .where(
            MovimientoDetalle.estante_origen_id == estante_id,
            Movimiento.tipo == TipoMovimiento.SALIDA,
        )
    )
    return _scalar_int(entradas) - _scalar_int(salidas)


def stock_articulo(articulo_id: int) -> int:
    stmt = (
        select(func.coalesce(func.sum(_saldo_expr()), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Lote, Lote.id == MovimientoDetalle.lote_id)
        .where(Lote.articulo_id == articulo_id)
    )
    return _scalar_int(stmt)


def stock_articulo_almacen(articulo_id: int, almacen_id: int) -> int:
    entradas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Lote, Lote.id == MovimientoDetalle.lote_id)
        .join(Estante, Estante.id == MovimientoDetalle.estante_destino_id)
        .where(
            Lote.articulo_id == articulo_id,
            Estante.almacen_id == almacen_id,
            Movimiento.tipo == TipoMovimiento.ENTRADA,
        )
    )
    salidas = (
        select(func.coalesce(func.sum(MovimientoDetalle.cantidad), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Lote, Lote.id == MovimientoDetalle.lote_id)
        .join(Estante, Estante.id == MovimientoDetalle.estante_origen_id)
        .where(
            Lote.articulo_id == articulo_id,
            Estante.almacen_id == almacen_id,
            Movimiento.tipo == TipoMovimiento.SALIDA,
        )
    )
    return _scalar_int(entradas) - _scalar_int(salidas)


def total_stock() -> int:
    stmt = (
        select(func.coalesce(func.sum(_saldo_expr()), 0))
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
    )
    return _scalar_int(stmt)


def listar_stock_lotes(query: str | None = None, solo_con_stock: bool = False) -> list[dict]:
    stock = func.coalesce(func.sum(_saldo_expr()), 0).label("stock")
    stmt = (
        select(
            Lote.id.label("lote_id"),
            Lote.numero_lote,
            Lote.fecha_fabricacion,
            Lote.fecha_vencimiento,
            Lote.proveedor,
            Articulo.id.label("articulo_id"),
            Articulo.codigo.label("codigo_articulo"),
            Articulo.nombre.label("nombre_articulo"),
            Articulo.unidad_medida,
            stock,
        )
        .select_from(Lote)
        .join(Articulo, Articulo.id == Lote.articulo_id)
        .outerjoin(MovimientoDetalle, MovimientoDetalle.lote_id == Lote.id)
        .outerjoin(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .group_by(
            Lote.id,
            Lote.numero_lote,
            Lote.fecha_fabricacion,
            Lote.fecha_vencimiento,
            Lote.proveedor,
            Articulo.id,
            Articulo.codigo,
            Articulo.nombre,
            Articulo.unidad_medida,
        )
        .order_by(Articulo.nombre, Lote.numero_lote)
    )
    if query:
        term = f"%{query.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Articulo.nombre).like(term)
            | func.lower(Articulo.codigo).like(term)
            | func.lower(Lote.numero_lote).like(term)
        )
    rows = db.session.execute(stmt).all()
    result = [dict(row._mapping) for row in rows]
    for item in result:
        item["stock"] = int(item["stock"] or 0)
    if solo_con_stock:
        result = [item for item in result if item["stock"] > 0]
    return result


def listar_stock_articulos(query: str | None = None, solo_bajo_stock: bool = False) -> list[dict]:
    stock = func.coalesce(func.sum(_saldo_expr()), 0).label("stock")
    stmt = (
        select(
            Articulo.id.label("articulo_id"),
            Articulo.codigo,
            Articulo.nombre,
            Articulo.unidad_medida,
            Articulo.stock_minimo,
            Categoria.nombre.label("categoria"),
            stock,
        )
        .select_from(Articulo)
        .outerjoin(Categoria, Categoria.id == Articulo.categoria_id)
        .outerjoin(Lote, Lote.articulo_id == Articulo.id)
        .outerjoin(MovimientoDetalle, MovimientoDetalle.lote_id == Lote.id)
        .outerjoin(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .group_by(
            Articulo.id,
            Articulo.codigo,
            Articulo.nombre,
            Articulo.unidad_medida,
            Articulo.stock_minimo,
            Categoria.nombre,
        )
        .order_by(Articulo.nombre)
    )
    if query:
        term = f"%{query.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Articulo.nombre).like(term)
            | func.lower(Articulo.codigo).like(term)
        )
    rows = db.session.execute(stmt).all()
    result = [dict(row._mapping) for row in rows]
    for item in result:
        item["stock"] = int(item["stock"] or 0)
        item["bajo_stock"] = (
            item["stock_minimo"] > 0 and item["stock"] <= item["stock_minimo"]
        )
    if solo_bajo_stock:
        result = [item for item in result if item["bajo_stock"]]
    return result


def listar_stock_almacenes() -> list[dict]:
    entradas = (
        select(
            Estante.almacen_id.label("almacen_id"),
            func.coalesce(func.sum(MovimientoDetalle.cantidad), 0).label("total"),
        )
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Estante, Estante.id == MovimientoDetalle.estante_destino_id)
        .where(Movimiento.tipo == TipoMovimiento.ENTRADA)
        .group_by(Estante.almacen_id)
        .subquery()
    )
    salidas = (
        select(
            Estante.almacen_id.label("almacen_id"),
            func.coalesce(func.sum(MovimientoDetalle.cantidad), 0).label("total"),
        )
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Estante, Estante.id == MovimientoDetalle.estante_origen_id)
        .where(Movimiento.tipo == TipoMovimiento.SALIDA)
        .group_by(Estante.almacen_id)
        .subquery()
    )
    stmt = (
        select(
            Almacen.id.label("almacen_id"),
            Almacen.codigo,
            Almacen.nombre,
            func.coalesce(entradas.c.total, 0).label("entradas"),
            func.coalesce(salidas.c.total, 0).label("salidas"),
            (
                func.coalesce(entradas.c.total, 0) - func.coalesce(salidas.c.total, 0)
            ).label("stock"),
        )
        .select_from(Almacen)
        .outerjoin(entradas, entradas.c.almacen_id == Almacen.id)
        .outerjoin(salidas, salidas.c.almacen_id == Almacen.id)
        .order_by(Almacen.nombre)
    )
    rows = db.session.execute(stmt).all()
    result = [dict(row._mapping) for row in rows]
    for item in result:
        item["entradas"] = int(item["entradas"] or 0)
        item["salidas"] = int(item["salidas"] or 0)
        item["stock"] = int(item["stock"] or 0)
    return result


def lotes_por_vencer(dias: int = 30) -> list[dict]:
    from datetime import date, timedelta

    limite = date.today() + timedelta(days=dias)
    items = listar_stock_lotes(solo_con_stock=True)
    return [
        item
        for item in items
        if item.get("fecha_vencimiento")
        and item["fecha_vencimiento"] <= limite
    ]


def stock_por_estante(estante_id: int) -> list[dict]:
    saldo = func.coalesce(
        func.sum(
            case(
                (
                    (Movimiento.tipo == TipoMovimiento.ENTRADA)
                    & (MovimientoDetalle.estante_destino_id == estante_id),
                    MovimientoDetalle.cantidad,
                ),
                (
                    (Movimiento.tipo == TipoMovimiento.SALIDA)
                    & (MovimientoDetalle.estante_origen_id == estante_id),
                    -MovimientoDetalle.cantidad,
                ),
                else_=0,
            )
        ),
        0,
    ).label("stock")
    stmt = (
        select(
            Lote.id.label("lote_id"),
            Lote.numero_lote,
            Articulo.codigo.label("codigo_articulo"),
            Articulo.nombre.label("nombre_articulo"),
            saldo,
        )
        .select_from(MovimientoDetalle)
        .join(Movimiento, Movimiento.id == MovimientoDetalle.movimiento_id)
        .join(Lote, Lote.id == MovimientoDetalle.lote_id)
        .join(Articulo, Articulo.id == Lote.articulo_id)
        .where(
            (MovimientoDetalle.estante_destino_id == estante_id)
            | (MovimientoDetalle.estante_origen_id == estante_id)
        )
        .group_by(Lote.id, Lote.numero_lote, Articulo.codigo, Articulo.nombre)
    )
    rows = db.session.execute(stmt).all()
    result = []
    for row in rows:
        item = dict(row._mapping)
        item["stock"] = int(item["stock"] or 0)
        if item["stock"] != 0:
            result.append(item)
    return result
