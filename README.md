# Bodega Control

Sistema de control de inventario multialmacén con stock dinámico. El stock **nunca** se guarda como un campo fijo: se calcula desde los movimientos históricos de entrada y salida.

## Stack

- Flask 3 con arquitectura de monolito modular
- SQLAlchemy + Flask-SQLAlchemy
- Flask-Migrate / Alembic
- Flask-Login y Flask-WTF
- MySQL 8 (configurado), con soporte para SQLite/PostgreSQL mediante `DATABASE_URL`
- Frontend HTML/CSS/JavaScript sin frameworks, en `frontend/`

## Estructura

```text
app/
  __init__.py          App factory
  registry.py          Registro de blueprints y modelos
  core/                Configuración, extensiones, errores, formularios, comandos
  modules/
    auth/
    dashboard/
    usuarios/
    almacenes/
    estantes/
    categorias/
    articulos/
    lotes/
    movimientos/
    stock/
frontend/
  templates/
  static/
migrations/            Migraciones Alembic
tests/                 Pruebas automatizadas
run.py                 Punto de entrada
```

Cada dominio en `app/modules/<dominio>/` contiene sus propios `models.py`, `services.py` y `routes.py`.

## Base de datos

La conexión se define en `.env`:

```env
DATABASE_URL=mysql+pymysql://usuario:clave@127.0.0.1:3306/multi_almacen?charset=utf8mb4
```

La base local `multi_almacen` ya fue creada y migrada. Para replicar el esquema en otra base:

```powershell
$env:FLASK_APP = "run.py"
.\.venv\Scripts\flask.exe db upgrade
.\.venv\Scripts\flask.exe seed-admin
```

Para generar una nueva migración después de cambiar modelos:

```powershell
$env:FLASK_APP = "run.py"
.\.venv\Scripts\flask.exe db migrate -m "descripcion del cambio"
.\.venv\Scripts\flask.exe db upgrade
```

## Ejecución

```powershell
.\.venv\Scripts\python.exe run.py
```

Abrir `http://127.0.0.1:8000`.

Credenciales iniciales:

- Usuario: `admin`
- Contraseña: `admin123`

Cambiar la contraseña y `SECRET_KEY` antes de usar el sistema en producción.

## Roles

- `ADMINISTRADOR`: gestiona usuarios, catálogos y movimientos.
- `JEFE_BODEGA`: gestiona catálogos y movimientos.
- `BODEGUERO`: registra y consulta movimientos.

## Stock dinámico

- `ENTRADA`: suma al estante destino. Requiere estante destino.
- `SALIDA`: resta del estante origen. Requiere estante origen y valida stock disponible por lote y estante.
- Una salida con destino se interpreta como transferencia entre estantes.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas usan SQLite en memoria y no modifican la base MySQL.

## Comandos útiles

```powershell
$env:FLASK_APP = "run.py"
.\.venv\Scripts\flask.exe seed-faker --count 10  # 10 registros Faker por tabla
.\.venv\Scripts\flask.exe seed-demo              # datos de demostración
.\.venv\Scripts\flask.exe db current             # revisión aplicada
.\.venv\Scripts\flask.exe db check               # diferencias modelo/esquema
```
