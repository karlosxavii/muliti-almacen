from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.articulos.models import Articulo
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote, LoteUbicacion


def listar(query: str | None = None, articulo_id: int | None = None):
    stmt = Lote.query.join(Articulo)
    if articulo_id:
        stmt = stmt.filter(Lote.articulo_id == articulo_id)
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Lote.numero_lote).like(term)
            | func.lower(Articulo.nombre).like(term)
            | func.lower(Articulo.codigo).like(term)
        )
    return stmt.order_by(Articulo.nombre, Lote.numero_lote)


def obtener(lote_id: int):
    return db.session.get(Lote, lote_id)


def crear(data: dict) -> Lote:
    articulo_id = data["articulo_id"]
    if not db.session.get(Articulo, articulo_id):
        raise DomainError("El artículo seleccionado no existe")
    if Lote.query.filter_by(
        articulo_id=articulo_id, numero_lote=data["numero_lote"]
    ).first():
        raise DomainError("Ya existe ese número de lote para el artículo")

    lote = Lote(
        numero_lote=data["numero_lote"],
        articulo_id=articulo_id,
        fecha_fabricacion=data.get("fecha_fabricacion"),
        fecha_vencimiento=data.get("fecha_vencimiento"),
        proveedor=data.get("proveedor") or None,
    )
    try:
        db.session.add(lote)
        db.session.flush()
        _guardar_ubicacion(
            lote, data.get("estante_id"), data.get("cantidad_inicial")
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        raise DomainError(str(exc)) from exc
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError("No se pudo crear el lote") from exc
    return lote


def actualizar(lote: Lote, data: dict) -> Lote:
    articulo_id = data["articulo_id"]
    if not db.session.get(Articulo, articulo_id):
        raise DomainError("El artículo seleccionado no existe")
    duplicate = Lote.query.filter(
        Lote.articulo_id == articulo_id,
        Lote.numero_lote == data["numero_lote"],
        Lote.id != lote.id,
    ).first()
    if duplicate:
        raise DomainError("Ya existe ese número de lote para el artículo")

    try:
        lote.numero_lote = data["numero_lote"]
        lote.articulo_id = articulo_id
        lote.fecha_fabricacion = data.get("fecha_fabricacion")
        lote.fecha_vencimiento = data.get("fecha_vencimiento")
        lote.proveedor = data.get("proveedor") or None
        _guardar_ubicacion(
            lote, data.get("estante_id"), data.get("cantidad_inicial")
        )
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        raise DomainError(str(exc)) from exc
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError("No se pudo actualizar el lote") from exc
    return lote


def eliminar(lote: Lote) -> None:
    try:
        db.session.delete(lote)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError("No se puede eliminar: el lote tiene movimientos asociados") from exc


def _guardar_ubicacion(lote: Lote, estante_id, cantidad_inicial) -> None:
    if not estante_id:
        return
    estante = db.session.get(Estante, estante_id)
    if not estante:
        raise DomainError("El estante seleccionado no existe")
    ubicacion = LoteUbicacion.query.filter_by(
        lote_id=lote.id, estante_id=estante.id
    ).first()
    if not ubicacion:
        ubicacion = LoteUbicacion(
            lote_id=lote.id,
            estante_id=estante.id,
            cantidad_inicial=cantidad_inicial or 0,
        )
        db.session.add(ubicacion)
    elif cantidad_inicial is not None:
        ubicacion.cantidad_inicial = cantidad_inicial


def lotes_por_vencer(dias: int = 30) -> list[Lote]:
    from datetime import timedelta

    limite = date.today() + timedelta(days=dias)
    return (
        Lote.query.filter(
            Lote.fecha_vencimiento.is_not(None), Lote.fecha_vencimiento <= limite
        )
        .order_by(Lote.fecha_vencimiento)
        .all()
    )
