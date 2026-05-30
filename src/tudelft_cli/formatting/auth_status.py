from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import AuthSession


console = Console()


def render_auth_status(session: AuthSession | None, as_json: bool = False) -> None:
    status = auth_status_to_dict(session)

    if as_json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    table = Table(title="Auth Status")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Authenticated", "yes" if status["authenticated"] else "no")
    table.add_row("Expires at", status["expires_at"] or "-")
    table.add_row("Expired", _status_bool(status["expired"]))

    console.print(table)


def auth_status_to_dict(session: AuthSession | None) -> dict[str, Any]:
    if session is None:
        return {
            "authenticated": False,
            "expires_at": None,
            "expired": None,
        }

    expired = _is_expired(session.expires_at)
    return {
        "authenticated": expired is not True,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "expired": expired,
    }


def _is_expired(expires_at: datetime | None) -> bool | None:
    if expires_at is None:
        return None

    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        now = now.replace(tzinfo=None)

    return expires_at <= now


def _status_bool(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "-"
