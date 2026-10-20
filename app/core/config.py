import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
INSTANCE_DIR = BASE_DIR / "instance"
FRONTEND_DIR = BASE_DIR / "frontend"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def default_database_url() -> str:
    return f"sqlite:///{(INSTANCE_DIR / 'bodega.db').as_posix()}"


def build_engine_options(database_url: str) -> dict:
    options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return options


DATABASE_URL = os.getenv("DATABASE_URL") or default_database_url()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "desarrollo-cambiar-esta-clave")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = build_engine_options(DATABASE_URL)
    SQLALCHEMY_EXPIRE_ON_COMMIT = False

    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", "20"))

    AUTO_CREATE_TABLES = env_bool("AUTO_CREATE_TABLES", True)
    AUTO_SEED_ADMIN = env_bool("AUTO_SEED_ADMIN", True)
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "Administrador")

    APP_NAME = os.getenv("APP_NAME", "Bodega Control")


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    AUTO_CREATE_TABLES = env_bool("AUTO_CREATE_TABLES", False)
    AUTO_SEED_ADMIN = env_bool("AUTO_SEED_ADMIN", False)


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    WTF_CSRF_ENABLED = False
    AUTO_CREATE_TABLES = True
    AUTO_SEED_ADMIN = True
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"
    DEFAULT_ADMIN_NAME = "Administrador de Pruebas"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
