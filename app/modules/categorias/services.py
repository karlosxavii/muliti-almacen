from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.categorias.models import Categoria


def listar(query: str | None = None):
    stmt = Categoria.query
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Categoria.codigo).like(term) | func.lower(Categoria.nombre).like(term)
        )
    return stmt.order_by(Categoria.nombre)


def obtener(categoria_id: int):
    return db.session.get(Categoria, categoria_id)


def crear(codigo: str, nombre: str, descripcion: str | None = None) -> Categoria:
    if Categoria.query.filter(func.lower(Categoria.codigo) == codigo.lower()).first():
        raise DomainError("El código de categoría ya existe")
    categoria = Categoria(codigo=codigo, nombre=nombre, descripcion=descripcion or None)
    db.session.add(categoria)
    _commit("No se pudo crear la categoría")
    return categoria


def actualizar(
    categoria: Categoria, codigo: str, nombre: str, descripcion: str | None = None
) -> Categoria:
    duplicate = Categoria.query.filter(
        func.lower(Categoria.codigo) == codigo.lower(), Categoria.id != categoria.id
    ).first()
    if duplicate:
        raise DomainError("Ya existe otra categoría con ese código")
    categoria.codigo = codigo
    categoria.nombre = nombre
    categoria.descripcion = descripcion or None
    _commit("No se pudo actualizar la categoría")
    return categoria


def eliminar(categoria: Categoria) -> None:
    db.session.delete(categoria)
    _commit("No se puede eliminar la categoría")


def _commit(message: str) -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(message) from exc
