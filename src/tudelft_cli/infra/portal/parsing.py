from __future__ import annotations

from datetime import datetime
from typing import Any, SupportsFloat, SupportsIndex

from tudelft_cli.domain.errors import PortalChangedError


def parse_bool_jn(value: object) -> bool | None:
    if value == "J":
        return True
    if value == "N":
        return False
    return None


def parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def required_string(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str):
        raise PortalChangedError(f"Result item is missing expected field: {key}")
    return value


def as_optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except ValueError:
        return None


def format_time_decimal(value: object) -> str | None:
    if value is None or value == "":
        return None

    if not isinstance(
        value,
        (str, bytes, bytearray, memoryview, SupportsFloat, SupportsIndex),
    ):
        return str(value)

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    hours = int(number)
    minutes = int(round((number - hours) * 60))
    return f"{hours:02d}:{minutes:02d}"
