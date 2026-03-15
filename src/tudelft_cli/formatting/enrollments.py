from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import CourseEnrollment


def render_course_enrollments_table(courses: list[CourseEnrollment], title: str = "Course enrollments") -> None:
    console = Console()
    table = Table(title=title)
    table.add_column("Code")
    table.add_column("Course")
    table.add_column("Block")
    table.add_column("Period")
    table.add_column("EC")
    table.add_column("Programme part")
    table.add_column("Can unenroll")

    for course in courses:
        ec_text = "-"
        if course.ec is not None:
            ec_text = f"{course.ec:g} {course.ec_unit or ''}".strip()

        table.add_row(
            course.course_code,
            course.course_name,
            course.block or "-",
            course.period_description or "-",
            ec_text,
            course.programme_part or "-",
            "yes" if course.can_unenroll else "no" if course.can_unenroll is not None else "-",
        )

    console.print(table)
