from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from tudelft_cli.domain.models import Grade


console = Console()


def render_grades(grades: list[Grade], pretty: bool = False, as_json: bool = False) -> None:
    if as_json:
        render_grades_json(grades)
    elif pretty:
        render_grades_pretty(grades)
    else:
        render_grades_table(grades)


def render_grades_table(grades: list[Grade]) -> None:
    table = Table(title="Grades")
    table.add_column("Course code")
    table.add_column("Course")
    table.add_column("Component")
    table.add_column("Grade")
    table.add_column("Passed")

    for item in grades:
        table.add_row(
            _text(item.course_code),
            _text(item.course_name),
            _text(item.component),
            _text(item.value),
            _passed_text(item.passed),
        )

    console.print(table)


def render_grades_pretty(grades: list[Grade]) -> None:
    if not grades:
        console.print(Panel("No grades available.", border_style="yellow"))
        return

    passed_count = sum(1 for item in grades if item.passed is True)
    failed_count = sum(1 for item in grades if item.passed is False)
    unknown_count = len(grades) - passed_count - failed_count

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold cyan", justify="right", no_wrap=True)
    summary.add_column()

    summary.add_row("Total", str(len(grades)))
    summary.add_row("Passed", f"[green]{passed_count}[/green]")
    summary.add_row("Failed", f"[red]{failed_count}[/red]")
    if unknown_count:
        summary.add_row("Other", str(unknown_count))

    console.print(
        Panel(
            summary,
            title=Text(" Grades Summary ", style="bold white"),
            border_style="bright_blue",
            expand=False,
            padding=(1, 2),
        )
    )

    table = Table(title="Grades")
    table.add_column("Code", style="bold")
    table.add_column("Course")
    table.add_column("Component")
    table.add_column("Grade", justify="center")
    table.add_column("Status", justify="center")

    for item in grades:
        table.add_row(
            _text(item.course_code),
            _text(item.course_name),
            _text(item.component),
            _grade_text(item.value, item.passed),
            _passed_rich_text(item.passed),
        )

    console.print(table)


def render_grades_json(grades: list[Grade]) -> None:
    print(json.dumps(_grades_to_dict(grades), indent=2, ensure_ascii=False))


def _grades_to_dict(grades: list[Grade]) -> dict[str, Any]:
    return {
        "items": [
            {
                "course_code": item.course_code,
                "course_name": item.course_name,
                "component": item.component,
                "value": item.value,
                "passed": item.passed,
                "published_at": item.published_at.isoformat() if item.published_at else None,
            }
            for item in grades
        ]
    }


def _text(value: str | None) -> str:
    if value is None:
        return "-"
    value = str(value).strip()
    return value if value else "-"


def _passed_text(value: bool | None) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "-"


def _passed_rich_text(value: bool | None) -> str:
    if value is True:
        return "[green]passed[/green]"
    if value is False:
        return "[red]failed[/red]"
    return "-"


def _grade_text(value: str | None, passed: bool | None) -> str:
    text = _text(value)
    if text == "-":
        return text
    if passed is True:
        return f"[green]{text}[/green]"
    if passed is False:
        return f"[red]{text}[/red]"
    return text