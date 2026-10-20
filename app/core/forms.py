from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import request

from app.core.errors import DomainError


class FormError(DomainError):
    pass


def form_str(name: str, default: str = "", max_length: int | None = None) -> str:
    value = (request.form.get(name) or default).strip()
    if max_length and len(value) > max_length:
        raise FormError(f"El campo {name} supera el máximo de {max_length} caracteres")
    return value


def form_required(name: str, label: str) -> str:
    value = form_str(name)
    if not value:
        raise FormError(f"El campo {label} es obligatorio")
    return value


def form_int(
    name: str,
    label: str,
    default: int | None = None,
    required: bool = False,
    min_value: int | None = None,
) -> int | None:
    raw = (request.form.get(name) or "").strip()
    if not raw:
        if required:
            raise FormError(f"El campo {label} es obligatorio")
        return default
    try:
        value = int(raw)
    except ValueError:
        raise FormError(f"El campo {label} debe ser numérico")
    if min_value is not None and value < min_value:
        raise FormError(f"El campo {label} debe ser mayor o igual a {min_value}")
    return value


def form_decimal(name: str, label: str) -> Decimal | None:
    raw = (request.form.get(name) or "").strip().replace(",", ".")
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise FormError(f"El campo {label} debe ser numérico")
    if value < 0:
        raise FormError(f"El campo {label} no puede ser negativo")
    return value


def form_date(name: str, label: str) -> date | None:
    raw = (request.form.get(name) or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise FormError(f"El campo {label} debe tener formato AAAA-MM-DD")


def form_bool(name: str) -> bool:
    return request.form.get(name) in {"1", "true", "on", "yes", "S"}


def form_list(name: str) -> list[str]:
    return request.form.getlist(name)
