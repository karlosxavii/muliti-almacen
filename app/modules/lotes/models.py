from datetime import date

from sqlalchemy.orm import validates

from app.core.base import BaseModel
from app.core.extensions import db


class Lote(BaseModel):
    __tablename__ = "lotes"
    __table_args__ = (
        db.UniqueConstraint("articulo_id", "numero_lote", name="uq_lote_articulo_numero"),
    )

    numero_lote = db.Column(db.String(100), nullable=False, index=True)
    articulo_id = db.Column(
        db.Integer,
        db.ForeignKey("articulos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fecha_fabricacion = db.Column(db.Date, nullable=True)
    fecha_vencimiento = db.Column(db.Date, nullable=True)
    proveedor = db.Column(db.String(150), nullable=True)

    articulo = db.relationship("Articulo", back_populates="lotes")
    ubicaciones = db.relationship(
        "LoteUbicacion",
        back_populates="lote",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    detalles = db.relationship(
        "MovimientoDetalle", back_populates="lote", passive_deletes=True
    )

    @validates("fecha_vencimiento")
    def validate_fecha_vencimiento(self, key, value):
        if value and self.fecha_fabricacion and value < self.fecha_fabricacion:
            raise ValueError("La fecha de vencimiento no puede ser anterior a la fabricación")
        return value

    @property
    def esta_vencido(self) -> bool:
        return bool(self.fecha_vencimiento and self.fecha_vencimiento < date.today())

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - date.today()).days

    @property
    def stock_disponible(self) -> int:
        from app.modules.stock.services import stock_lote

        return stock_lote(self.id)

    def __repr__(self):
        return f"<Lote {self.numero_lote}>"


class LoteUbicacion(BaseModel):
    __tablename__ = "lote_ubicaciones"
    __table_args__ = (
        db.UniqueConstraint("lote_id", "estante_id", name="uq_lote_estante"),
        db.CheckConstraint("cantidad_inicial >= 0", name="ck_lote_ubicacion_cantidad"),
    )

    lote_id = db.Column(
        db.Integer,
        db.ForeignKey("lotes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estante_id = db.Column(
        db.Integer,
        db.ForeignKey("estantes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cantidad_inicial = db.Column(db.Integer, nullable=False, default=0)

    lote = db.relationship("Lote", back_populates="ubicaciones")
    estante = db.relationship("Estante", back_populates="lote_ubicaciones")

    def __repr__(self):
        return f"<LoteUbicacion lote={self.lote_id} estante={self.estante_id}>"
