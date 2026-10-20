from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.articulos.models import Articulo
from app.modules.categorias.models import Categoria


def listar(query: str | None = None, categoria_id: int | None = None):
    stmt = Articulo.query
    if categoria_id:
        stmt = stmt.filter(Articulo.categoria_id == categoria_id)
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Articulo.codigo).like(term) | func.lower(Articulo.nombre).like(term)
        )
    return stmt.order_by(Articulo.nombre)


def obtener(articulo_id: int):
    return db.session.get(Articulo, articulo_id)


def crear(data: dict) -> Articulo:
    _validar(data)
    if Articulo.query.filter(func.lower(Articulo.codigo) == data["codigo"].lower()).first():
        raise DomainError("El código de artículo ya existe")
    articulo = Articulo(**data)
    db.session.add(articulo)
    _commit("No se pudo crear el artículo")
    return articulo


def actualizar(articulo: Articulo, data: dict) -> Articulo:
    _validar(data)
    duplicate = Articulo.query.filter(
        func.lower(Articulo.codigo) == data["codigo"].lower(), Articulo.id != articulo.id
    ).first()
    if duplicate:
        raise DomainError("Ya existe otro artículo con ese código")
    for field, value in data.items():
        setattr(articulo, field, value)
    _commit("No se pudo actualizar el artículo")
    return articulo


def eliminar(articulo: Articulo) -> None:
    db.session.delete(articulo)
    _commit("No se puede eliminar: el artículo tiene movimientos asociados")


def _validar(data: dict) -> None:
    if data.get("categoria_id") and not db.session.get(Categoria, data["categoria_id"]):
        raise DomainError("La categoría seleccionada no existe")


def _commit(message: str) -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(message) from exc
