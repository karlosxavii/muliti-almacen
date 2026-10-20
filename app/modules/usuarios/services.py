from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.usuarios.models import RolUsuario, Usuario


def listar(query: str | None = None):
    stmt = Usuario.query
    if query:
        term = f"%{query.lower()}%"
        stmt = stmt.filter(
            func.lower(Usuario.username).like(term)
            | func.lower(Usuario.nombre_completo).like(term)
        )
    return stmt.order_by(Usuario.nombre_completo)


def obtener(usuario_id: int):
    return db.session.get(Usuario, usuario_id)


def crear(
    username: str,
    nombre_completo: str,
    password: str,
    rol: RolUsuario,
    activo: bool = True,
) -> Usuario:
    if Usuario.query.filter(func.lower(Usuario.username) == username.lower()).first():
        raise DomainError("El nombre de usuario ya existe")
    usuario = Usuario(
        username=username,
        nombre_completo=nombre_completo,
        rol=rol,
        activo=activo,
    )
    usuario.set_password(password)
    db.session.add(usuario)
    _commit("No se pudo crear el usuario")
    return usuario


def actualizar(
    usuario: Usuario,
    username: str,
    nombre_completo: str,
    rol: RolUsuario,
    activo: bool,
    password: str | None,
    current_user_id: int,
) -> Usuario:
    duplicate = Usuario.query.filter(
        func.lower(Usuario.username) == username.lower(), Usuario.id != usuario.id
    ).first()
    if duplicate:
        raise DomainError("Ya existe otro usuario con ese nombre")
    if usuario.id == current_user_id and not activo:
        raise DomainError("No puedes desactivar tu propio usuario")

    usuario.username = username
    usuario.nombre_completo = nombre_completo
    usuario.rol = rol
    usuario.activo = activo
    if password:
        usuario.set_password(password)
    _commit("No se pudo actualizar el usuario")
    return usuario


def cambiar_estado(usuario: Usuario, current_user_id: int) -> Usuario:
    if usuario.id == current_user_id:
        raise DomainError("No puedes cambiar el estado de tu propio usuario")
    usuario.activo = not usuario.activo
    _commit("No se pudo cambiar el estado del usuario")
    return usuario


def _commit(message: str) -> None:
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(message) from exc
