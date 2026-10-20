import unittest

from app import create_app
from app.core.extensions import db
from app.modules.almacenes.models import Almacen
from app.modules.articulos.models import Articulo
from app.modules.categorias.models import Categoria
from app.modules.estantes.models import Estante
from app.modules.lotes.models import Lote, LoteUbicacion
from app.modules.movimientos.models import Movimiento
from app.modules.usuarios.models import RolUsuario, Usuario


class CrudTest(unittest.TestCase):
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
        response = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def _crear_almacen(self, codigo="ALM-1"):
        self.client.post(
            "/almacenes/crear",
            data={"codigo": codigo, "nombre": "Almacén principal", "descripcion": "Test"},
            follow_redirects=True,
        )
        with self.app.app_context():
            return Almacen.query.filter_by(codigo=codigo).one().id

    def _crear_categoria(self, codigo="CAT-1"):
        self.client.post(
            "/categorias/crear",
            data={"codigo": codigo, "nombre": "Categoría", "descripcion": ""},
            follow_redirects=True,
        )
        with self.app.app_context():
            return Categoria.query.filter_by(codigo=codigo).one().id

    def _crear_articulo(self, codigo="ART-1", categoria_id=None):
        self.client.post(
            "/articulos/crear",
            data={
                "codigo": codigo,
                "nombre": "Artículo",
                "descripcion": "",
                "unidad_medida": "UNIDAD",
                "categoria_id": str(categoria_id or ""),
                "peso_kg": "1.5",
                "precio_unitario": "10.25",
                "stock_minimo": "3",
                "activo": "1",
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            return Articulo.query.filter_by(codigo=codigo).one().id

    def _crear_estante(self, almacen_id, codigo="E-1"):
        self.client.post(
            "/estantes/crear",
            data={
                "codigo": codigo,
                "nombre": "Estante",
                "descripcion": "",
                "almacen_id": str(almacen_id),
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            return Estante.query.filter_by(codigo=codigo).one().id

    def _crear_lote(self, articulo_id, estante_id, numero="LOT-1"):
        self.client.post(
            "/lotes/crear",
            data={
                "numero_lote": numero,
                "articulo_id": str(articulo_id),
                "fecha_fabricacion": "2026-01-01",
                "fecha_vencimiento": "2027-01-01",
                "proveedor": "Proveedor",
                "estante_id": str(estante_id),
                "cantidad_inicial": "10",
            },
            follow_redirects=True,
        )
        with self.app.app_context():
            return Lote.query.filter_by(numero_lote=numero).one().id

    def test_crud_almacen(self):
        self._crear_almacen()
        with self.app.app_context():
            almacen = Almacen.query.filter_by(codigo="ALM-1").one()
            almacen_id = almacen.id

        response = self.client.post(
            f"/almacenes/{almacen_id}/editar",
            data={"codigo": "ALM-2", "nombre": "Almacén editado", "descripcion": "Nueva"},
            follow_redirects=True,
        )
        self.assertIn("actualizado", response.get_data(as_text=True))
        with self.app.app_context():
            almacen = db.session.get(Almacen, almacen_id)
            self.assertEqual(almacen.codigo, "ALM-2")
            self.assertEqual(almacen.nombre, "Almacén editado")

        response = self.client.post(f"/almacenes/{almacen_id}/eliminar", follow_redirects=True)
        self.assertIn("eliminado", response.get_data(as_text=True))
        with self.app.app_context():
            self.assertIsNone(db.session.get(Almacen, almacen_id))

    def test_crud_estante(self):
        almacen_id = self._crear_almacen()
        estante_id = self._crear_estante(almacen_id)
        with self.app.app_context():
            estante = db.session.get(Estante, estante_id)
            self.assertEqual(estante.almacen_id, almacen_id)

        response = self.client.post(
            f"/estantes/{estante_id}/editar",
            data={
                "codigo": "E-2",
                "nombre": "Estante editado",
                "descripcion": "Nueva",
                "almacen_id": str(almacen_id),
            },
            follow_redirects=True,
        )
        self.assertIn("actualizado", response.get_data(as_text=True))
        with self.app.app_context():
            estante = db.session.get(Estante, estante_id)
            self.assertEqual(estante.codigo, "E-2")
            self.assertEqual(estante.nombre, "Estante editado")

        self.client.post(f"/estantes/{estante_id}/eliminar", follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Estante, estante_id))

    def test_crud_categoria(self):
        categoria_id = self._crear_categoria()
        response = self.client.post(
            f"/categorias/{categoria_id}/editar",
            data={"codigo": "CAT-2", "nombre": "Categoría editada", "descripcion": "Nueva"},
            follow_redirects=True,
        )
        self.assertIn("actualizada", response.get_data(as_text=True))
        with self.app.app_context():
            categoria = db.session.get(Categoria, categoria_id)
            self.assertEqual(categoria.codigo, "CAT-2")

        self.client.post(f"/categorias/{categoria_id}/eliminar", follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Categoria, categoria_id))

    def test_crud_articulo(self):
        categoria_id = self._crear_categoria()
        articulo_id = self._crear_articulo(categoria_id=categoria_id)

        response = self.client.post(
            f"/articulos/{articulo_id}/editar",
            data={
                "codigo": "ART-2",
                "nombre": "Artículo editado",
                "descripcion": "Nueva",
                "unidad_medida": "CAJA",
                "categoria_id": str(categoria_id),
                "peso_kg": "2.5",
                "precio_unitario": "20.50",
                "stock_minimo": "8",
            },
            follow_redirects=True,
        )
        self.assertIn("actualizado", response.get_data(as_text=True))
        with self.app.app_context():
            articulo = db.session.get(Articulo, articulo_id)
            self.assertEqual(articulo.codigo, "ART-2")
            self.assertEqual(articulo.unidad_medida, "CAJA")
            self.assertFalse(articulo.activo)
            self.assertEqual(float(articulo.precio_unitario), 20.50)

        self.client.post(f"/articulos/{articulo_id}/eliminar", follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Articulo, articulo_id))

    def test_crud_lote_y_ubicacion(self):
        almacen_id = self._crear_almacen()
        estante_id = self._crear_estante(almacen_id)
        categoria_id = self._crear_categoria()
        articulo_id = self._crear_articulo(categoria_id=categoria_id)
        lote_id = self._crear_lote(articulo_id, estante_id)

        with self.app.app_context():
            self.assertEqual(LoteUbicacion.query.filter_by(lote_id=lote_id).count(), 1)

        response = self.client.post(
            f"/lotes/{lote_id}/editar",
            data={
                "numero_lote": "LOT-2",
                "articulo_id": str(articulo_id),
                "fecha_fabricacion": "2026-02-01",
                "fecha_vencimiento": "2027-02-01",
                "proveedor": "Proveedor editado",
                "estante_id": str(estante_id),
                "cantidad_inicial": "25",
            },
            follow_redirects=True,
        )
        self.assertIn("actualizado", response.get_data(as_text=True))
        with self.app.app_context():
            lote = db.session.get(Lote, lote_id)
            self.assertEqual(lote.numero_lote, "LOT-2")
            self.assertEqual(lote.proveedor, "Proveedor editado")
            ubicacion = LoteUbicacion.query.filter_by(lote_id=lote_id).one()
            self.assertEqual(ubicacion.cantidad_inicial, 25)

        self.client.post(f"/lotes/{lote_id}/eliminar", follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(db.session.get(Lote, lote_id))
            self.assertEqual(LoteUbicacion.query.filter_by(lote_id=lote_id).count(), 0)

    def test_crud_usuario_y_estado(self):
        response = self.client.post(
            "/usuarios/crear",
            data={
                "username": "operador",
                "nombre_completo": "Operador de prueba",
                "password": "clave123",
                "rol": RolUsuario.BODEGUERO.value,
                "activo": "1",
            },
            follow_redirects=True,
        )
        self.assertIn("creado", response.get_data(as_text=True))
        with self.app.app_context():
            usuario = Usuario.query.filter_by(username="operador").one()
            usuario_id = usuario.id
            self.assertTrue(usuario.check_password("clave123"))

        response = self.client.post(
            f"/usuarios/{usuario_id}/editar",
            data={
                "username": "operador2",
                "nombre_completo": "Operador editado",
                "password": "nueva123",
                "rol": RolUsuario.JEFE_BODEGA.value,
                "activo": "1",
            },
            follow_redirects=True,
        )
        self.assertIn("actualizado", response.get_data(as_text=True))
        with self.app.app_context():
            usuario = db.session.get(Usuario, usuario_id)
            self.assertEqual(usuario.username, "operador2")
            self.assertEqual(usuario.rol, RolUsuario.JEFE_BODEGA)
            self.assertTrue(usuario.check_password("nueva123"))

        self.client.post(f"/usuarios/{usuario_id}/estado", follow_redirects=True)
        with self.app.app_context():
            self.assertFalse(db.session.get(Usuario, usuario_id).activo)

        self.client.post(f"/usuarios/{usuario_id}/estado", follow_redirects=True)
        with self.app.app_context():
            self.assertTrue(db.session.get(Usuario, usuario_id).activo)

        with self.app.app_context():
            admin_id = Usuario.query.filter_by(username="admin").one().id
        response = self.client.post(
            f"/usuarios/{admin_id}/editar",
            data={
                "username": "admin",
                "nombre_completo": "Administrador",
                "rol": RolUsuario.ADMINISTRADOR.value,
            },
            follow_redirects=True,
        )
        self.assertIn("No puedes desactivar tu propio usuario", response.get_data(as_text=True))
        with self.app.app_context():
            self.assertTrue(db.session.get(Usuario, admin_id).activo)

    def test_movimiento_crear_y_consultar(self):
        almacen_id = self._crear_almacen()
        estante_id = self._crear_estante(almacen_id)
        categoria_id = self._crear_categoria()
        articulo_id = self._crear_articulo(categoria_id=categoria_id)
        lote_id = self._crear_lote(articulo_id, estante_id)

        response = self.client.post(
            "/movimientos/registrar",
            data={
                "tipo": "ENTRADA",
                "documento": "DOC-1",
                "observacion": "Entrada",
                "fecha_movimiento": "2026-10-19",
                "detalle_lote": [str(lote_id)],
                "detalle_cantidad": ["12"],
                "detalle_origen": [""],
                "detalle_destino": [str(estante_id)],
                "detalle_precio": ["10.00"],
            },
            follow_redirects=True,
        )
        self.assertIn("Movimiento registrado", response.get_data(as_text=True))
        with self.app.app_context():
            movimiento = Movimiento.query.filter_by(documento="DOC-1").one()
            movimiento_id = movimiento.id
            self.assertEqual(movimiento.total_unidades, 12)
            self.assertEqual(len(movimiento.detalles), 1)

        self.assertEqual(self.client.get(f"/movimientos/{movimiento_id}").status_code, 200)
        self.assertIn(
            self.client.post(f"/movimientos/{movimiento_id}/eliminar").status_code,
            {404, 405},
        )
        self.assertIn(
            self.client.post(f"/movimientos/{movimiento_id}/editar").status_code,
            {404, 405},
        )


if __name__ == "__main__":
    unittest.main()
