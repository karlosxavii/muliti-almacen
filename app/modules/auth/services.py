from datetime import datetime

from app.core.extensions import db
from app.modules.usuarios.models import Usuario


def autenticar(username: str, password: str) -> Usuario | None:
    user = Usuario.query.filter_by(username=username).first()
    if not user or not user.activo:
        return None
    if not user.check_password(password):
        return None
    return user


def registrar_acceso(user: Usuario) -> None:
    user.ultimo_acceso = datetime.now()
    db.session.commit()
