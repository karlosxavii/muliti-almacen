import unittest

from app import create_app
from app.core.extensions import db
from app.modules.almacenes.models import Almacen
from app.modules.articulos.models import Articulo
from app.modules.categorias.models import Categoria
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote
from app.modules.movimientos.models import Movimiento
from app.modules.stock import services as stock_service
from app.modules.usuarios.models import Usuario


class SmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app("testing")
        cls.client = cls.app.test_client()

    def setUp(self):
        with self.client.session_transaction() as session:
            session.clear()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            from app.core.commands import ensure_default_admin

            ensure_default_admin(self.app)

    def login(self):
        response = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_flujo_completo(self):
        self.login()

        for url in [
            "/",
            "/almacenes/",
            "/almacenes/crear",
            "/estantes/",
            "/estantes/crear",
            "/categorias/",
            "/categorias/crear",
            "/articulos/",
            "/articulos/crear",
            "/lotes/",
            "/lotes/crear",
            "/movimientos/",
            "/movimientos/registrar",
            "/stock/lotes",
            "/stock/articulos",
            "/stock/almacenes",
            "/usuarios/",
            "/usuarios/crear",
            "/health",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

        with self.client.get("/static/css/styles.css") as response:
            self.assertEqual(response.status_code, 200)
        with self.client.get("/static/js/movimientos.js") as response:
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/almacenes/crear",
            data={"codigo": "ALM-T", "nombre": "Almacén de prueba", "descripcion": "Test"},
            follow_redirects=True,
        )
        self.assertIn("creado correctamente", response.get_data(as_text=True))

        with self.app.app_context():
            almacen = Almacen.query.filter_by(codigo="ALM-T").first()
            self.assertIsNotNone(almacen)
            almacen_id = almacen.id

        self.client.post(
            "/estantes/crear",
            data={
                "codigo": "E1",
                "nombre": "Estante 1",
                "descripcion": "",
                "almacen_id": str(almacen_id),
            },
            follow_redirects=True,
        )
        self.client.post(
            "/categorias/crear",
            data={"codigo": "CAT-T", "nombre": "Categoría test", "descripcion": ""},
            follow_redirects=True,
        )

        with self.app.app_context():
            estante = Estante.query.filter_by(codigo="E1").first()
            categoria = Categoria.query.filter_by(codigo="CAT-T").first()
            self.assertIsNotNone(estante)
            self.assertIsNotNone(categoria)
            estante_id = estante.id
            categoria_id = categoria.id

        self.client.post(
            "/articulos/crear",
            data={
                "codigo": "ART-T",
                "nombre": "Artículo de prueba",
                "descripcion": "",
                "unidad_medida": "UNIDAD",
                "categoria_id": str(categoria_id),
                "peso_kg": "",
                "precio_unitario": "10.50",
                "stock_minimo": "5",
                "activo": "1",
            },
            follow_redirects=True,
        )

        with self.app.app_context():
            articulo = Articulo.query.filter_by(codigo="ART-T").first()
            self.assertIsNotNone(articulo)
            articulo_id = articulo.id

        self.client.post(
            "/lotes/crear",
            data={
                "numero_lote": "LOT-T",
                "articulo_id": str(articulo_id),
                "fecha_fabricacion": "2026-01-01",
                "fecha_vencimiento": "2027-01-01",
                "proveedor": "Proveedor test",
                "estante_id": str(estante_id),
                "cantidad_inicial": "0",
            },
            follow_redirects=True,
        )

        with self.app.app_context():
            lote = Lote.query.filter_by(numero_lote="LOT-T").first()
            self.assertIsNotNone(lote)
            lote_id = lote.id

        response = self.client.post(
            "/movimientos/registrar",
            data={
                "tipo": "ENTRADA",
                "documento": "OC-T",
                "observacion": "Entrada de prueba",
                "fecha_movimiento": "2026-10-19",
                "detalle_lote": [str(lote_id)],
                "detalle_cantidad": ["25"],
                "detalle_origen": [""],
                "detalle_destino": [str(estante_id)],
                "detalle_precio": ["10.50"],
            },
            follow_redirects=True,
        )
        self.assertIn("Movimiento registrado", response.get_data(as_text=True))

        with self.app.app_context():
            self.assertEqual(stock_service.stock_lote(lote_id), 25)
            self.assertEqual(stock_service.stock_articulo(articulo_id), 25)
            self.assertEqual(stock_service.stock_lote_estante(lote_id, estante_id), 25)
            movimiento = Movimiento.query.order_by(Movimiento.id.desc()).first()
            self.assertIsNotNone(movimiento)
            movimiento_id = movimiento.id

        response = self.client.post(
            "/movimientos/registrar",
            data={
                "tipo": "SALIDA",
                "documento": "REQ-T",
                "observacion": "Salida de prueba",
                "fecha_movimiento": "2026-10-19",
                "detalle_lote": [str(lote_id)],
                "detalle_cantidad": ["10"],
                "detalle_origen": [str(estante_id)],
                "detalle_destino": [""],
                "detalle_precio": [""],
            },
            follow_redirects=True,
        )
        self.assertIn("Movimiento registrado", response.get_data(as_text=True))

        with self.app.app_context():
            self.assertEqual(stock_service.stock_lote(lote_id), 15)
            self.assertEqual(stock_service.stock_articulo(articulo_id), 15)

        response = self.client.post(
            "/movimientos/registrar",
            data={
                "tipo": "SALIDA",
                "documento": "REQ-T2",
                "observacion": "Salida inválida",
                "fecha_movimiento": "2026-10-19",
                "detalle_lote": [str(lote_id)],
                "detalle_cantidad": ["999"],
                "detalle_origen": [str(estante_id)],
                "detalle_destino": [""],
                "detalle_precio": [""],
            },
            follow_redirects=True,
        )
        self.assertIn("Stock insuficiente", response.get_data(as_text=True))

        self.assertEqual(self.client.get(f"/movimientos/{movimiento_id}").status_code, 200)
        self.assertEqual(self.client.get("/stock/lotes?q=ART-T").status_code, 200)
        self.assertEqual(self.client.get("/stock/articulos?bajo=1").status_code, 200)
        self.assertEqual(self.client.get("/stock/almacenes").status_code, 200)

        response = self.client.post(
            "/usuarios/crear",
            data={
                "username": "operador",
                "nombre_completo": "Operador de prueba",
                "password": "clave123",
                "rol": "BODEGUERO",
                "activo": "1",
            },
            follow_redirects=True,
        )
        self.assertIn("Usuario creado", response.get_data(as_text=True))

        with self.app.app_context():
            self.assertIsNotNone(Usuario.query.filter_by(username="operador").first())

    def test_requiere_login(self):
        self.client.post("/auth/logout")
        response = self.client.get("/almacenes/", follow_redirects=False)
        self.assertIn(response.status_code, {302, 401})


if __name__ == "__main__":
    unittest.main()
