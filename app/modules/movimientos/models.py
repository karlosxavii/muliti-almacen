import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import validates

from app.core.base import BaseModel
from app.core.enums import enum_values
from app.core.extensions import db


class TipoMovimiento(str, enum.Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"

    @classmethod
    def choices(cls):
        return [(item.value, item.value.capitalize()) for item in cls]


class Movimiento(BaseModel):
    __tablename__ = "movimientos"
    __table_args__ = (
        db.Index("ix_movimientos_tipo_fecha", "tipo", "fecha_movimiento"),
    )

    tipo = db.Column(
        db.Enum(
            TipoMovimiento,
            values_callable=enum_values,
            native_enum=False,
            length=20,
            validate_strings=True,
        ),
        nullable=False,
    )
    documento = db.Column(db.String(100), nullable=True)
    observacion = db.Column(db.Text, nullable=True)
    fecha_movimiento = db.Column(db.DateTime, nullable=False, default=datetime.now)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    usuario = db.relationship("Usuario", back_populates="movimientos")
    detalles = db.relationship(
        "MovimientoDetalle",
        back_populates="movimiento",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def total_unidades(self) -> int:
        return sum(detalle.cantidad for detalle in self.detalles)

    @property
    def total_valor(self):
        return sum(detalle.subtotal for detalle in self.detalles)

    @property
    def resumen(self) -> str:
        return f"{self.tipo.value} · {len(self.detalles)} línea(s) · {self.total_unidades} unidades"

    def __repr__(self):
        return f"<Movimiento {self.id} {self.tipo}>"


class MovimientoDetalle(BaseModel):
    __tablename__ = "movimiento_detalles"
    __table_args__ = (
        db.CheckConstraint("cantidad > 0", name="ck_movimiento_detalle_cantidad"),
    )

    movimiento_id = db.Column(
        db.Integer,
        db.ForeignKey("movimientos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lote_id = db.Column(
        db.Integer,
        db.ForeignKey("lotes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    estante_origen_id = db.Column(
        db.Integer,
        db.ForeignKey("estantes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    estante_destino_id = db.Column(
        db.Integer,
        db.ForeignKey("estantes.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=True)
    observacion = db.Column(db.Text, nullable=True)

    movimiento = db.relationship("Movimiento", back_populates="detalles")
    lote = db.relationship("Lote", back_populates="detalles")
    estante_origen = db.relationship("Estante", foreign_keys=[estante_origen_id])
    estante_destino = db.relationship("Estante", foreign_keys=[estante_destino_id])

    @validates("cantidad")
    def validate_cantidad(self, key, value):
        if value is None or int(value) <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return int(value)

    @property
    def subtotal(self) -> Decimal:
        if self.precio_unitario is None:
            return Decimal("0")
        return Decimal(self.precio_unitario) * self.cantidad

    def __repr__(self):
        return f"<MovimientoDetalle lote={self.lote_id} cantidad={self.cantidad}>"
