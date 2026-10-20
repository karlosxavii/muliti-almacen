from flask import Blueprint, render_template
from flask_login import login_required

from app.modules.dashboard import services as dashboard_service

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    return render_template(
        "dashboard.html",
        resumen=dashboard_service.resumen(),
        bajo_stock=dashboard_service.articulos_bajo_stock(),
        recientes=dashboard_service.movimientos_recientes(),
        por_vencer=dashboard_service.proximos_vencimientos(),
    )
