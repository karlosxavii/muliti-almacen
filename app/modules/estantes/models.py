from app.core.base import BaseModel
from app.core.extensions import db


class Estante(BaseModel):
    __tablename__ = "estantes"
    __table_args__ = (
        db.UniqueConstraint("almacen_id", "codigo", name="uq_estante_almacen_codigo"),
    )

    codigo = db.Column(db.String(50), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    almacen_id = db.Column(
        db.Integer,
        db.ForeignKey("almacenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    almacen = db.relationship("Almacen", back_populates="estantes")
    lote_ubicaciones = db.relationship(
        "LoteUbicacion",
        back_populates="estante",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def nombre_completo(self) -> str:
        base = f"{self.almacen.codigo}/{self.codigo}" if self.almacen else self.codigo
        return f"{base} - {self.nombre}" if self.nombre else base

    @property
    def stock_disponible(self) -> int:
        from app.modules.stock.services import stock_estante

        return stock_estante(self.id)

    def __repr__(self):
        return f"<Estante {self.codigo}>"
