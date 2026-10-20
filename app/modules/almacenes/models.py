from app.core.base import BaseModel
from app.core.extensions import db


class Almacen(BaseModel):
    __tablename__ = "almacenes"

    codigo = db.Column(db.String(50), unique=True, index=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

    estantes = db.relationship(
        "Estante",
        back_populates="almacen",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def total_estantes(self) -> int:
        return len(self.estantes)

    def __repr__(self):
        return f"<Almacen {self.codigo}>"
