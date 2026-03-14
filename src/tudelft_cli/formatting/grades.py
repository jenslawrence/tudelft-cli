from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import Grade


def render_grades_table(grades: list[Grade]) -> None:
    console = Console()
    table = Table(title="Grades")
    table.add_column("Course code")
    table.add_column("Course")
    table.add_column("Component")
    table.add_column("Grade")
    table.add_column("Passed")

    for grade in grades:
        table.add_row(
            grade.course_code,
            grade.course_name,
            grade.component,
            grade.value,
            "yes" if grade.passed else "no" if grade.passed is not None else "-",
        )

    console.print(table)


def render_grades_json(grades: list[Grade]) -> None:
    serializable = [_grade_to_dict(grade) for grade in grades]
    print(json.dumps(serializable, indent=2, ensure_ascii=False))


def _grade_to_dict(grade: Grade) -> dict[str, Any]:
    return {
        "course_code": grade.course_code,
        "course_name": grade.course_name,
        "component": grade.component,
        "value": grade.value,
        "passed": grade.passed,
        "published_at": _serialize_datetime(grade.published_at),
    }


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
