import os

from flask import Flask, jsonify, render_template

from app.core.config import CONFIG_MAP, FRONTEND_DIR, INSTANCE_DIR
from app.core.extensions import csrf, db, login_manager, migrate
from app.core.pagination import page_url
from app.registry import BLUEPRINTS, import_models


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_CONFIG", "development")
    config_class = CONFIG_MAP.get(config_name, CONFIG_MAP["development"])

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=False,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar"
    login_manager.login_message_category = "warning"

    register_blueprints(app)
    register_commands(app)
    register_template_helpers(app)
    register_error_handlers(app)
    register_healthcheck(app)

    with app.app_context():
        from app.core.commands import ensure_default_admin

        import_models()
        if app.config.get("AUTO_CREATE_TABLES"):
            db.create_all()
        if app.config.get("AUTO_SEED_ADMIN"):
            ensure_default_admin(app)

    return app


def register_blueprints(app: Flask) -> None:
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)


def register_commands(app: Flask) -> None:
    from app.core.commands import register_commands as _register

    _register(app)


def register_template_helpers(app: Flask) -> None:
    from app.modules.movimientos.models import TipoMovimiento
    from app.modules.usuarios.models import RolUsuario

    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": app.config["APP_NAME"],
            "RolUsuario": RolUsuario,
            "TipoMovimiento": TipoMovimiento,
        }

    @app.template_filter("money")
    def money_filter(value):
        if value is None:
            return "—"
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "—"

    @app.template_filter("fecha")
    def fecha_filter(value):
        return value.strftime("%d/%m/%Y") if value else "—"

    @app.template_filter("fecha_hora")
    def fecha_hora_filter(value):
        return value.strftime("%d/%m/%Y %H:%M") if value else "—"

    @app.template_filter("numero")
    def numero_filter(value):
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return "0"

    app.jinja_env.globals["page_url"] = page_url


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(401)
    def unauthorized(error):
        return render_template("errors/403.html", mensaje="Debes iniciar sesión"), 401

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", mensaje="No tienes permisos para esta acción"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500


def register_healthcheck(app: Flask) -> None:
    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "app": app.config["APP_NAME"]})
