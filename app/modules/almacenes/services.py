from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.almacenes.models import Almacen


def listar(query: str | None = None):
    stmt = Almacen.query
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Almacen.codigo).like(term) | func.lower(Almacen.nombre).like(term)
        )
    return stmt.order_by(Almacen.nombre)


def obtener(almacen_id: int):
    return db.session.get(Almacen, almacen_id)


def crear(codigo: str, nombre: str, descripcion: str | None = None) -> Almacen:
    if Almacen.query.filter(func.lower(Almacen.codigo) == codigo.lower()).first():
        raise DomainError("El código de almacén ya existe")
    almacen = Almacen(codigo=codigo, nombre=nombre, descripcion=descripcion or None)
    db.session.add(almacen)
    _commit("No se pudo crear el almacén")
    return almacen


def actualizar(
    almacen: Almacen, codigo: str, nombre: str, descripcion: str | None = None
) -> Almacen:
    duplicate = Almacen.query.filter(
        func.lower(Almacen.codigo) == codigo.lower(), Almacen.id != almacen.id
    ).first()
    if duplicate:
        raise DomainError("Ya existe otro almacén con ese código")
    almacen.codigo = codigo
    almacen.nombre = nombre
    almacen.descripcion = descripcion or None
    _commit("No se pudo actualizar el almacén")
    return almacen


def eliminar(almacen: Almacen) -> None:
    db.session.delete(almacen)
    _commit("No se puede eliminar: tiene estantes con movimientos asociados")


def _commit(message: str) -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(message) from exc
