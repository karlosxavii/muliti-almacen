from functools import wraps

from flask import abort
from flask_login import current_user

from app.modules.usuarios.models import RolUsuario


def role_required(*roles):
    allowed = {role if isinstance(role, RolUsuario) else RolUsuario(role) for role in roles}

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.rol not in allowed:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


catalog_required = role_required(RolUsuario.ADMINISTRADOR, RolUsuario.JEFE_BODEGA)
admin_required = role_required(RolUsuario.ADMINISTRADOR)
