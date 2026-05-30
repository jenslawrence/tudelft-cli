from __future__ import annotations

from datetime import datetime
from typing import Any, SupportsFloat, SupportsIndex

from tudelft_cli.domain.errors import PortalChangedError

_MISSING = object()


def _type_name(value: object) -> str:
    return type(value).__name__


def _schema_error(context: str, field: str, expected: str, value: object = _MISSING) -> PortalChangedError:
    if value is _MISSING:
        detail = "field is missing"
    else:
        detail = f"got {_type_name(value)}"
    return PortalChangedError(
        f"Portal response changed while parsing {context}: field '{field}' "
        f"expected {expected}; {detail}."
    )


def required_field(
    data: dict[str, Any],
    field: str,
    context: str,
    expected: str = "a value",
) -> object:
    if field not in data:
        raise _schema_error(context, field, expected)
    value = data[field]
    if value is None:
        raise _schema_error(context, field, expected, value)
    return value


def optional_field(data: dict[str, Any], field: str, default: object = None) -> object:
    value = data.get(field, default)
    if value is None:
        return default
    return value


def required_str(data: dict[str, Any], field: str, context: str) -> str:
    value = required_field(data, field, context, "str")
    if not isinstance(value, str):
        raise _schema_error(context, field, "str", value)
    return value


def optional_str(data: dict[str, Any], field: str, default: str | None = None) -> str | None:
    value = optional_field(data, field, default)
    if value is default:
        return default
    if not isinstance(value, str):
        raise _schema_error("portal item", field, "str", value)
    return value


def _to_int(value: object, field: str, context: str) -> int:
    if isinstance(value, bool):
        raise _schema_error(context, field, "int", value)
    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise _schema_error(context, field, "int", value) from exc


def required_int(data: dict[str, Any], field: str, context: str) -> int:
    return _to_int(required_field(data, field, context, "int"), field, context)


def optional_int(
    data: dict[str, Any],
    field: str,
    context: str = "portal item",
    default: int | None = None,
) -> int | None:
    value = data.get(field)
    if value is None or value == "":
        return default
    return _to_int(value, field, context)


def _to_float(value: object, field: str, context: str) -> float:
    if isinstance(value, bool):
        raise _schema_error(context, field, "float", value)
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise _schema_error(context, field, "float", value) from exc


def optional_float(
    data: dict[str, Any],
    field: str,
    context: str = "portal item",
    default: float | None = None,
) -> float | None:
    value = data.get(field)
    if value is None or value == "":
        return default
    return _to_float(value, field, context)


def required_list(data: dict[str, Any], field: str, context: str) -> list[Any]:
    value = required_field(data, field, context, "list")
    if not isinstance(value, list):
        raise _schema_error(context, field, "list", value)
    return value


def required_dict(data: dict[str, Any], field: str, context: str) -> dict[str, Any]:
    value = required_field(data, field, context, "dict")
    if not isinstance(value, dict):
        raise _schema_error(context, field, "dict", value)
    return value


def require_dict_item(item: object, context: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise PortalChangedError(
            f"Portal response changed while parsing {context}: expected dict item; "
            f"got {_type_name(item)}."
        )
    return item


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
    return required_str(item, key, "portal item")


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
