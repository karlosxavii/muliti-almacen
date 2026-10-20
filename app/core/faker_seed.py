from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.core.extensions import db
from app.modules.almacenes import services as almacen_service
from app.modules.almacenes.models import Almacen
from app.modules.articulos import services as articulo_service
from app.modules.articulos.models import Articulo
from app.modules.categorias import services as categoria_service
from app.modules.categorias.models import Categoria
from app.modules.estantes import services as estante_service
from app.modules.estantes.models import Estante
from app.modules.lotes import services as lote_service
from app.modules.lotes.models import Lote, LoteUbicacion
from app.modules.movimientos import services as movimiento_service
from app.modules.movimientos.models import Movimiento, MovimientoDetalle
from app.modules.usuarios import services as usuario_service
from app.modules.usuarios.models import RolUsuario, Usuario

FAKER_PREFIX = "FKR-"
FAKER_USER_PREFIX = "fkr_"
FAKER_PASSWORD = "Faker123!"

UNIDADES = ["UNIDAD", "CAJA", "KG", "LITRO", "PAQUETE", "BULTO"]


def clear_faker_data() -> None:
    movement_ids = [
        row[0]
        for row in db.session.query(Movimiento.id)
        .filter(Movimiento.documento.like(f"{FAKER_PREFIX}%"))
        .all()
    ]
    lote_ids = [
        row[0]
        for row in db.session.query(Lote.id)
        .filter(Lote.numero_lote.like(f"{FAKER_PREFIX}%"))
        .all()
    ]

    try:
        if movement_ids:
            MovimientoDetalle.query.filter(
                MovimientoDetalle.movimiento_id.in_(movement_ids)
            ).delete(synchronize_session=False)
            Movimiento.query.filter(Movimiento.id.in_(movement_ids)).delete(
                synchronize_session=False
            )
        if lote_ids:
            LoteUbicacion.query.filter(LoteUbicacion.lote_id.in_(lote_ids)).delete(
                synchronize_session=False
            )
            Lote.query.filter(Lote.id.in_(lote_ids)).delete(synchronize_session=False)
        Articulo.query.filter(Articulo.codigo.like(f"{FAKER_PREFIX}%")).delete(
            synchronize_session=False
        )
        Categoria.query.filter(Categoria.codigo.like(f"{FAKER_PREFIX}%")).delete(
            synchronize_session=False
        )
        Estante.query.filter(Estante.codigo.like(f"{FAKER_PREFIX}%")).delete(
            synchronize_session=False
        )
        Almacen.query.filter(Almacen.codigo.like(f"{FAKER_PREFIX}%")).delete(
            synchronize_session=False
        )
        Usuario.query.filter(Usuario.username.like(f"{FAKER_USER_PREFIX}%")).delete(
            synchronize_session=False
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DomainError(
            "No se pudieron limpiar los datos Faker porque tienen movimientos "
            "manuales asociados"
        ) from exc


def seed_faker(count: int = 10, reset: bool = True, seed: int = 20261019) -> dict:
    if count < 1:
        raise DomainError("La cantidad debe ser mayor que cero")

    fake = Faker("es_ES")
    fake.seed_instance(seed)
    rng = Random(seed)

    if reset:
        clear_faker_data()

    admin = Usuario.query.filter_by(username="admin").first()
    if admin is None:
        admin = Usuario.query.filter_by(rol=RolUsuario.ADMINISTRADOR).first()
    if admin is None:
        raise DomainError("No hay un usuario administrador para asociar los movimientos")

    almacenes = []
    estantes = []
    categorias = []
    articulos = []
    lotes_con_estante = []

    for index in range(1, count + 1):
        almacen = almacen_service.crear(
            codigo=f"{FAKER_PREFIX}ALM-{index:02d}",
            nombre=f"Almacén {fake.city()} {index:02d}",
            descripcion=fake.sentence(nb_words=10),
        )
        almacenes.append(almacen)

    for index in range(1, count + 1):
        estante = estante_service.crear(
            codigo=f"{FAKER_PREFIX}EST-{index:02d}",
            nombre=f"Estante {fake.word().capitalize()} {index:02d}",
            descripcion=fake.sentence(nb_words=8),
            almacen_id=almacenes[(index - 1) % len(almacenes)].id,
        )
        estantes.append(estante)

    for index in range(1, count + 1):
        categoria = categoria_service.crear(
            codigo=f"{FAKER_PREFIX}CAT-{index:02d}",
            nombre=f"{fake.word().capitalize()} {index:02d}",
            descripcion=fake.sentence(nb_words=8),
        )
        categorias.append(categoria)

    for index in range(1, count + 1):
        articulo = articulo_service.crear(
            {
                "codigo": f"{FAKER_PREFIX}ART-{index:02d}",
                "nombre": f"{fake.word().capitalize()} {fake.word()} {index:02d}",
                "descripcion": fake.sentence(nb_words=12),
                "unidad_medida": rng.choice(UNIDADES),
                "categoria_id": categorias[(index - 1) % len(categorias)].id,
                "peso_kg": round(rng.uniform(0.1, 50), 3),
                "precio_unitario": round(rng.uniform(1, 500), 2),
                "stock_minimo": rng.randint(2, 20),
                "activo": True,
            }
        )
        articulos.append(articulo)

    for index in range(1, count + 1):
        fabricacion = fake.date_between(start_date="-2y", end_date="-60d")
        vencimiento = fake.date_between(start_date="+90d", end_date="+2y")
        estante = estantes[(index - 1) % len(estantes)]
        lote = lote_service.crear(
            {
                "numero_lote": f"{FAKER_PREFIX}LOT-{index:02d}",
                "articulo_id": articulos[(index - 1) % len(articulos)].id,
                "fecha_fabricacion": fabricacion,
                "fecha_vencimiento": vencimiento,
                "proveedor": fake.company(),
                "estante_id": estante.id,
                "cantidad_inicial": rng.randint(0, 100),
            }
        )
        lotes_con_estante.append((lote, estante))

    for index in range(1, count + 1):
        if index == 1:
            rol = RolUsuario.ADMINISTRADOR
        elif index <= 3:
            rol = RolUsuario.JEFE_BODEGA
        else:
            rol = RolUsuario.BODEGUERO
        usuario_service.crear(
            username=f"{FAKER_USER_PREFIX}{index:02d}",
            nombre_completo=fake.name(),
            password=FAKER_PASSWORD,
            rol=rol,
            activo=True,
        )

    entradas = max(1, count // 2)
    salidas = count - entradas
    cantidades_entrada = {}

    for index in range(entradas):
        lote, estante = lotes_con_estante[index % len(lotes_con_estante)]
        cantidad = rng.randint(100, 500)
        cantidades_entrada[lote.id] = cantidad
        fecha = fake.date_time_between(start_date="-90d", end_date="-15d")
        movimiento_service.registrar_movimiento(
            tipo="ENTRADA",
            usuario_id=admin.id,
            detalles=[
                {
                    "lote_id": lote.id,
                    "cantidad": cantidad,
                    "estante_destino_id": estante.id,
                    "precio_unitario": round(rng.uniform(1, 100), 2),
                }
            ],
            documento=f"{FAKER_PREFIX}ENT-{index + 1:02d}",
            observacion=fake.sentence(nb_words=8),
            fecha_movimiento=fecha,
        )

    for index in range(salidas):
        lote, estante = lotes_con_estante[index % len(lotes_con_estante)]
        disponible = cantidades_entrada.get(lote.id, 0)
        cantidad = rng.randint(1, max(1, min(40, disponible // 2)))
        fecha = datetime.now() - timedelta(days=rng.randint(1, 10), hours=rng.randint(0, 6))
        movimiento_service.registrar_movimiento(
            tipo="SALIDA",
            usuario_id=admin.id,
            detalles=[
                {
                    "lote_id": lote.id,
                    "cantidad": cantidad,
                    "estante_origen_id": estante.id,
                }
            ],
            documento=f"{FAKER_PREFIX}SAL-{index + 1:02d}",
            observacion=fake.sentence(nb_words=8),
            fecha_movimiento=fecha,
        )

    return {
        "almacenes": len(almacenes),
        "estantes": len(estantes),
        "categorias": len(categorias),
        "articulos": len(articulos),
        "lotes": len(lotes_con_estante),
        "lote_ubicaciones": LoteUbicacion.query.filter(
            LoteUbicacion.lote_id.in_([lote.id for lote, _ in lotes_con_estante])
        ).count(),
        "usuarios": Usuario.query.filter(Usuario.username.like(f"{FAKER_USER_PREFIX}%")).count(),
        "movimientos": Movimiento.query.filter(
            Movimiento.documento.like(f"{FAKER_PREFIX}%")
        ).count(),
        "movimiento_detalles": MovimientoDetalle.query.join(Movimiento)
        .filter(Movimiento.documento.like(f"{FAKER_PREFIX}%"))
        .count(),
    }
