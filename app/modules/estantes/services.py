from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.almacenes.models import Almacen
from app.modules.estantes.models import Estante


def listar(query: str | None = None, almacen_id: int | None = None):
    stmt = Estante.query.join(Almacen)
    if almacen_id:
        stmt = stmt.filter(Estante.almacen_id == almacen_id)
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Estante.codigo).like(term)
            | func.lower(Estante.nombre).like(term)
            | func.lower(Almacen.nombre).like(term)
        )
    return stmt.order_by(Almacen.nombre, Estante.codigo)


def obtener(estante_id: int):
    return db.session.get(Estante, estante_id)


def crear(
    codigo: str,
    nombre: str | None,
    descripcion: str | None,
    almacen_id: int,
) -> Estante:
    if not db.session.get(Almacen, almacen_id):
        raise DomainError("El almacén seleccionado no existe")
    if Estante.query.filter_by(almacen_id=almacen_id, codigo=codigo).first():
        raise DomainError("Ya existe un estante con ese código en el almacén")
    estante = Estante(
        codigo=codigo,
        nombre=nombre or None,
        descripcion=descripcion or None,
        almacen_id=almacen_id,
    )
    db.session.add(estante)
    _commit("No se pudo crear el estante")
    return estante


def actualizar(
    estante: Estante,
    codigo: str,
    nombre: str | None,
    descripcion: str | None,
    almacen_id: int,
) -> Estante:
    if not db.session.get(Almacen, almacen_id):
        raise DomainError("El almacén seleccionado no existe")
    duplicate = Estante.query.filter(
        Estante.almacen_id == almacen_id,
        Estante.codigo == codigo,
        Estante.id != estante.id,
    ).first()
    if duplicate:
        raise DomainError("Ya existe un estante con ese código en el almacén")
    estante.codigo = codigo
    estante.nombre = nombre or None
    estante.descripcion = descripcion or None
    estante.almacen_id = almacen_id
    _commit("No se pudo actualizar el estante")
    return estante


def eliminar(estante: Estante) -> None:
    db.session.delete(estante)
    _commit("No se puede eliminar: el estante tiene movimientos asociados")


def _commit(message: str) -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(message) from exc
