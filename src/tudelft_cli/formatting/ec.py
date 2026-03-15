from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tudelft_cli.domain.models import EcProgress


console = Console()


def render_ec(progress: EcProgress, pretty: bool = False, as_json: bool = False) -> None:
    if as_json:
        render_ec_json(progress)
    elif pretty:
        render_ec_pretty(progress)
    else:
        render_ec_table(progress)


def render_ec_table(progress: EcProgress) -> None:
    table = Table(title="EC Progress")
    table.add_column("Programme")
    table.add_column("Phase")
    table.add_column("Earned EC")
    table.add_column("Required EC")
    table.add_column("Progress")
    table.add_column("Completed")

    for item in progress.items:
        progress_text = f"{item.percentage}%" if item.percentage is not None else "-"
        earned_text = str(item.earned_ec) if item.earned_ec is not None else "-"
        required_text = str(item.required_ec) if item.required_ec is not None else "-"
        completed_text = (
            "yes" if item.completed else "no" if item.completed is not None else "-"
        )

        table.add_row(
            item.programme_name,
            item.phase_description,
            earned_text,
            required_text,
            progress_text,
            completed_text,
        )

    console.print(table)


def render_ec_pretty(progress: EcProgress) -> None:
    if not progress.items:
        console.print(Panel("No EC progress data available.", border_style="yellow"))
        return

    for item in progress.items:
        programme = _text(item.programme_name)
        phase = _text(item.phase_description)
        earned = _num(item.earned_ec)
        required = _num(item.required_ec)
        percentage = item.percentage if item.percentage is not None else 0

        body = Table.grid(padding=(0, 2))
        body.add_column(style="bold cyan", justify="right", no_wrap=True)
        body.add_column()

        body.add_row("Phase", phase)
        body.add_row("Progress", f"{earned} / {required} EC")
        body.add_row("Bar", _progress_bar(percentage))

        console.print(
            Panel(
                body,
                title=Text(f" {programme} ", style="bold white"),
                border_style=_border_style(item.completed, percentage),
                expand=False,
                padding=(1, 2),
            )
        )


def render_ec_json(progress: EcProgress) -> None:
    print(json.dumps(_ec_to_dict(progress), indent=2, ensure_ascii=False))


def _ec_to_dict(progress: EcProgress) -> dict[str, Any]:
    return {
        "items": [
            {
                "programme_name": item.programme_name,
                "faculty": item.faculty,
                "exam_programme_name": item.exam_programme_name,
                "phase_description": item.phase_description,
                "earned_ec": item.earned_ec,
                "required_ec": item.required_ec,
                "percentage": item.percentage,
                "completed": item.completed,
                "other_earned_ec": item.other_earned_ec,
            }
            for item in progress.items
        ]
    }


def _progress_bar(percentage: int | float) -> str:
    percentage = max(0, min(100, int(percentage)))
    width = 24
    filled = round((percentage / 100) * width)
    empty = width - filled
    return f"[green]{'█' * filled}[/green][grey35]{'█' * empty}[/grey35] {percentage}%"


def _border_style(completed: bool | None, percentage: int | float | None) -> str:
    if completed is True:
        return "green"
    if percentage is None:
        return "bright_blue"
    if percentage >= 50:
        return "bright_blue"
    return "yellow"


def _completed_text(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "-"


def _text(value: str | None) -> str:
    if value is None:
        return "-"
    value = value.strip()
    return value if value else "-"


def _num(value: int | float | None) -> str:
    if value is None:
        return "-"
    return str(value)