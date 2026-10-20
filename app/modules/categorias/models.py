from app.core.base import BaseModel
from app.core.extensions import db


class Categoria(BaseModel):
    __tablename__ = "categorias"

    codigo = db.Column(db.String(50), unique=True, index=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)

    articulos = db.relationship("Articulo", back_populates="categoria")

    @property
    def total_articulos(self) -> int:
        return len(self.articulos)

    def __repr__(self):
        return f"<Categoria {self.codigo}>"
