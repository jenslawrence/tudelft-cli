from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import SuggestedCourse


def render_suggested_courses_table(courses: list[SuggestedCourse]) -> None:
    console = Console()
    table = Table(title="Suggested courses")
    table.add_column("Code")
    table.add_column("Course")
    table.add_column("Block")
    table.add_column("Period")
    table.add_column("EC")
    table.add_column("Faculty")

    for course in courses:
        ec_text = "-"
        if course.ec is not None:
            ec_text = f"{course.ec} {course.ec_unit or ''}".strip()

        table.add_row(
            course.course_code,
            course.course_name,
            course.block or "-",
            course.period_description or "-",
            ec_text,
            course.faculty or "-",
        )

    console.print(table)


def render_suggested_courses_json(courses: list[SuggestedCourse]) -> None:
    print(json.dumps([_to_dict(course) for course in courses], indent=2, ensure_ascii=False))


def _to_dict(course: SuggestedCourse) -> dict[str, Any]:
    return {
        "course_offering_id": course.course_offering_id,
        "course_id": course.course_id,
        "course_code": course.course_code,
        "academic_year": course.academic_year,
        "block": course.block,
        "period_description": course.period_description,
        "period_date_range": course.period_date_range,
        "course_name": course.course_name,
        "faculty": course.faculty,
        "category": course.category,
        "ec": course.ec,
        "ec_unit": course.ec_unit,
        "availability": course.availability,
        "waiting_list": course.waiting_list,
    }
