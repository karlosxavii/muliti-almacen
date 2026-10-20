from app.core.base import BaseModel
from app.core.extensions import db


class Articulo(BaseModel):
    __tablename__ = "articulos"

    codigo = db.Column(db.String(100), unique=True, index=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    unidad_medida = db.Column(db.String(50), nullable=False, default="UNIDAD")
    peso_kg = db.Column(db.Numeric(10, 3), nullable=True)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=True)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categorias.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    categoria = db.relationship("Categoria", back_populates="articulos")
    lotes = db.relationship(
        "Lote",
        back_populates="articulo",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def stock_total(self) -> int:
        from app.modules.stock.services import stock_articulo

        return stock_articulo(self.id)

    @property
    def bajo_stock(self) -> bool:
        return self.stock_minimo > 0 and self.stock_total <= self.stock_minimo

    def __repr__(self):
        return f"<Articulo {self.codigo}>"
