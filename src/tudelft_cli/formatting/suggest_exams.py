import json
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import SuggestedExamCourse

console = Console()


def render_suggested_exams_table(courses: list[SuggestedExamCourse]) -> None:
    table = Table(title="Suggested exams")
    table.add_column("Code")
    table.add_column("Course")
    table.add_column("EC")
    table.add_column("Programme part")

    for course in courses:
        ec_text = "-"
        if course.ec is not None:
            ec_text = f"{course.ec:g} {course.ec_unit or ''}".strip()

        table.add_row(
            course.course_code,
            course.course_name,
            ec_text,
            course.programme_part or "-",
        )

    console.print(table)


def render_suggested_exams_json(courses: list[SuggestedExamCourse]) -> None:
    print(json.dumps([_to_dict(item) for item in courses], indent=2, ensure_ascii=False))


def _to_dict(item: SuggestedExamCourse) -> dict[str, Any]:
    return {
        "course_id": item.course_id,
        "course_code": item.course_code,
        "academic_year": item.academic_year,
        "course_name": item.course_name,
        "ec": item.ec,
        "ec_unit": item.ec_unit,
        "faculty": item.faculty,
        "category": item.category,
        "course_type": item.course_type,
        "programme_part": item.programme_part,
    }
