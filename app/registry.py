from app.modules.almacenes.models import Almacen
from app.modules.almacenes.routes import bp as almacenes_bp
from app.modules.articulos.models import Articulo
from app.modules.articulos.routes import bp as articulos_bp
from app.modules.auth.routes import bp as auth_bp
from app.modules.categorias.models import Categoria
from app.modules.categorias.routes import bp as categorias_bp
from app.modules.dashboard.routes import bp as dashboard_bp
from app.modules.estantes.models import Estante
from app.modules.estantes.routes import bp as estantes_bp
from app.modules.lotes.models import Lote, LoteUbicacion
from app.modules.lotes.routes import bp as lotes_bp
from app.modules.movimientos.models import (
    Movimiento,
    MovimientoDetalle,
    TipoMovimiento,
)
from app.modules.movimientos.routes import bp as movimientos_bp
from app.modules.stock.routes import bp as stock_bp
from app.modules.usuarios.models import RolUsuario, Usuario
from app.modules.usuarios.routes import bp as usuarios_bp

BLUEPRINTS = [
    dashboard_bp,
    auth_bp,
    almacenes_bp,
    estantes_bp,
    categorias_bp,
    articulos_bp,
    lotes_bp,
    movimientos_bp,
    stock_bp,
    usuarios_bp,
]

MODELS = [
    Almacen,
    Estante,
    Categoria,
    Articulo,
    Lote,
    LoteUbicacion,
    Movimiento,
    MovimientoDetalle,
    Usuario,
]


def import_models():
    return MODELS


__all__ = ["BLUEPRINTS", "MODELS", "import_models"]
