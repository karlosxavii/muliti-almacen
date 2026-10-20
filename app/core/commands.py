from __future__ import annotations

from datetime import datetime

import click
from flask import Flask
from flask.cli import with_appcontext

from app.core.extensions import db
from app.modules.articulos.models import Articulo
from app.modules.almacenes.models import Almacen
from app.modules.categorias.models import Categoria
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.usuarios.models import RolUsuario, Usuario


def ensure_default_admin(app: Flask) -> None:
    username = app.config["DEFAULT_ADMIN_USERNAME"]
    user = Usuario.query.filter_by(username=username).first()
    if user:
        return
    user = Usuario(
        username=username,
        nombre_completo=app.config["DEFAULT_ADMIN_NAME"],
        rol=RolUsuario.ADMINISTRADOR,
        activo=True,
    )
    user.set_password(app.config["DEFAULT_ADMIN_PASSWORD"])
    db.session.add(user)
    db.session.commit()


def ensure_user(username: str, password: str, nombre: str, rol: RolUsuario) -> Usuario:
    user = Usuario.query.filter_by(username=username).first()
    if user:
        return user
    user = Usuario(username=username, nombre_completo=nombre, rol=rol, activo=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def register_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        db.create_all()
        click.echo("Tablas creadas")

    @app.cli.command("seed-admin")
    @click.option("--username", default=None)
    @click.option("--password", default=None)
    @click.option("--nombre", default=None)
    @with_appcontext
    def seed_admin_command(username, password, nombre):
        username = username or app.config["DEFAULT_ADMIN_USERNAME"]
        password = password or app.config["DEFAULT_ADMIN_PASSWORD"]
        nombre = nombre or app.config["DEFAULT_ADMIN_NAME"]
        if Usuario.query.filter_by(username=username).first():
            click.echo(f"El usuario {username} ya existe")
            return
        user = Usuario(
            username=username,
            nombre_completo=nombre,
            rol=RolUsuario.ADMINISTRADOR,
            activo=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuario administrador {username} creado")

    @app.cli.command("seed-faker")
    @click.option("--count", default=10, show_default=True, type=click.IntRange(min=1, max=100))
    @click.option("--no-reset", is_flag=True, help="No elimina los datos Faker anteriores")
    @click.option("--seed", default=20261019, show_default=True)
    @with_appcontext
    def seed_faker_command(count, no_reset, seed):
        from app.core.faker_seed import seed_faker

        result = seed_faker(count=count, reset=not no_reset, seed=seed)
        for table, total in result.items():
            click.echo(f"{table}: {total}")
        click.echo("Datos Faker creados correctamente")

    @app.cli.command("seed-demo")
    @with_appcontext
    def seed_demo_command():
        from app.modules.movimientos.services import registrar_movimiento
        from app.modules.stock import services as stock_service

        ensure_user("jefe", "jefe123", "Jefe de Bodega", RolUsuario.JEFE_BODEGA)
        ensure_user("bodeguero", "bode123", "Bodeguero", RolUsuario.BODEGUERO)

        if Articulo.query.count() > 0:
            click.echo("Ya existen artículos; no se generaron datos de ejemplo")
            return

        almacen_principal = Almacen(codigo="ALM-01", nombre="Almacén principal")
        almacen_secundario = Almacen(codigo="ALM-02", nombre="Almacén secundario")
        db.session.add_all([almacen_principal, almacen_secundario])
        db.session.flush()

        estantes = [
            Estante(codigo="A1", nombre="Pasillo A", almacen_id=almacen_principal.id),
            Estante(codigo="A2", nombre="Pasillo B", almacen_id=almacen_principal.id),
            Estante(codigo="B1", nombre="Zona seca", almacen_id=almacen_secundario.id),
        ]
        db.session.add_all(estantes)

        categoria = Categoria(codigo="GEN", nombre="General")
        db.session.add(categoria)
        db.session.flush()

        articulos = [
            Articulo(codigo="ART-001", nombre="Caja de guantes", categoria_id=categoria.id, stock_minimo=10),
            Articulo(codigo="ART-002", nombre="Botiquín", categoria_id=categoria.id, stock_minimo=5),
            Articulo(codigo="ART-003", nombre="Extintor", categoria_id=categoria.id, stock_minimo=2),
        ]
        db.session.add_all(articulos)
        db.session.commit()

        lotes = []
        for index, articulo in enumerate(articulos, start=1):
            lote = Lote(
                numero_lote=f"LOT-{index:03d}",
                articulo_id=articulo.id,
                proveedor="Proveedor demo",
                fecha_fabricacion=datetime(2026, 1, index).date(),
                fecha_vencimiento=datetime(2027, 1, index).date(),
            )
            db.session.add(lote)
            lotes.append(lote)
        db.session.commit()

        admin = Usuario.query.filter_by(username=app.config["DEFAULT_ADMIN_USERNAME"]).first()
        registrar_movimiento(
            "ENTRADA",
            admin.id if admin else None,
            [
                {"lote_id": lotes[0].id, "cantidad": 50, "estante_destino_id": estantes[0].id},
                {"lote_id": lotes[1].id, "cantidad": 30, "estante_destino_id": estantes[1].id},
                {"lote_id": lotes[2].id, "cantidad": 10, "estante_destino_id": estantes[2].id},
            ],
            documento="OC-0001",
            observacion="Carga inicial de demostración",
        )
        registrar_movimiento(
            "SALIDA",
            admin.id if admin else None,
            [{"lote_id": lotes[0].id, "cantidad": 12, "estante_origen_id": estantes[0].id}],
            documento="REQ-0001",
            observacion="Consumo de demostración",
        )

        for articulo in articulos:
            click.echo(f"{articulo.codigo}: {stock_service.stock_articulo(articulo.id)} unidades")
        click.echo("Datos de ejemplo creados")
