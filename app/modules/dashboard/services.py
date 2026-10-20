from sqlalchemy.orm import joinedload, selectinload

from app.modules.almacenes.models import Almacen
from app.modules.articulos.models import Articulo
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.movimientos.models import Movimiento, MovimientoDetalle
from app.modules.stock.services import listar_stock_articulos, lotes_por_vencer, total_stock
from app.modules.usuarios.models import Usuario


def resumen() -> dict:
    return {
        "almacenes": Almacen.query.count(),
        "estantes": Estante.query.count(),
        "articulos": Articulo.query.count(),
        "lotes": Lote.query.count(),
        "usuarios": Usuario.query.count(),
        "stock": total_stock(),
        "movimientos": Movimiento.query.count(),
    }


def movimientos_recientes(limite: int = 8):
    return (
        Movimiento.query.options(
            joinedload(Movimiento.usuario),
            selectinload(Movimiento.detalles).joinedload(MovimientoDetalle.lote),
        )
        .order_by(Movimiento.fecha_movimiento.desc())
        .limit(limite)
        .all()
    )


def articulos_bajo_stock(limite: int = 8) -> list[dict]:
    return [item for item in listar_stock_articulos() if item["bajo_stock"]][:limite]


def proximos_vencimientos(dias: int = 30, limite: int = 6) -> list[dict]:
    return lotes_por_vencer(dias)[:limite]
