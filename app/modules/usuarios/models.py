import enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.base import BaseModel
from app.core.enums import enum_values
from app.core.extensions import db


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    JEFE_BODEGA = "JEFE_BODEGA"
    BODEGUERO = "BODEGUERO"

    @classmethod
    def choices(cls):
        return [(item.value, cls.labels()[item]) for item in cls]

    @classmethod
    def labels(cls):
        return {
            cls.ADMINISTRADOR: "Administrador",
            cls.JEFE_BODEGA: "Jefe de bodega",
            cls.BODEGUERO: "Bodeguero",
        }


class Usuario(BaseModel, UserMixin):
    __tablename__ = "usuarios"

    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    rol = db.Column(
        db.Enum(
            RolUsuario,
            values_callable=enum_values,
            native_enum=False,
            length=30,
            validate_strings=True,
        ),
        nullable=False,
        default=RolUsuario.BODEGUERO,
    )
    activo = db.Column(db.Boolean, nullable=False, default=True)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)

    movimientos = db.relationship(
        "Movimiento", back_populates="usuario", passive_deletes=True
    )

    def set_password(self, password: str):
        if not password or len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        return bool(self.activo)

    @property
    def is_admin(self) -> bool:
        return self.rol == RolUsuario.ADMINISTRADOR

    @property
    def is_jefe(self) -> bool:
        return self.rol == RolUsuario.JEFE_BODEGA

    @property
    def can_manage_catalogs(self) -> bool:
        return self.rol in (RolUsuario.ADMINISTRADOR, RolUsuario.JEFE_BODEGA)

    @property
    def can_manage_users(self) -> bool:
        return self.rol == RolUsuario.ADMINISTRADOR

    @property
    def rol_label(self) -> str:
        return RolUsuario.labels().get(self.rol, str(self.rol))

    def to_dict(self, exclude=None):
        data = super().to_dict(exclude=exclude)
        data.pop("password_hash", None)
        data["rol"] = self.rol.value if self.rol else None
        return data

    def __repr__(self):
        return f"<Usuario {self.username}>"
