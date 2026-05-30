import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tudelft_cli.domain.models import StudentProfile


console = Console()


def render_profile(
    profile: StudentProfile,
    pretty: bool = False,
    as_json: bool = False,
) -> None:
    if as_json:
        render_profile_json(profile)
    elif pretty:
        _render_profile_pretty(profile)
    else:
        _render_profile_plain(profile)


def render_profile_json(profile: StudentProfile) -> None:
    print(json.dumps(_profile_to_dict(profile), indent=2, ensure_ascii=False))


def _profile_to_dict(profile: StudentProfile) -> dict[str, Any]:
    return {
        "profile": {
            "name": profile.name,
            "student_number": profile.student_number,
            "email": profile.email,
        }
    }


def _render_profile_plain(profile: StudentProfile) -> None:
    table = Table(title="Student Profile")

    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Name", _value(profile.name))
    table.add_row("Student number", _value(profile.student_number))
    table.add_row("Email", _value(profile.email))

    console.print(table)


def _render_profile_pretty(profile: StudentProfile) -> None:
    body = Table.grid(padding=(0, 2))
    body.add_column(style="bold cyan", justify="right", no_wrap=True)
    body.add_column()

    body.add_row("Name", _value(profile.name))
    body.add_row("Student number", _value(profile.student_number))
    body.add_row("Email", _value(profile.email))

    console.print(
        Panel(
            body,
            title=Text(" Student Profile ", style="bold white"),
            border_style="bright_blue",
            expand=False,
            padding=(1, 2),
        )
    )


def _value(value: str | None) -> str:
    if value is None:
        return "-"
    value = value.strip()
    return value if value else "-"
