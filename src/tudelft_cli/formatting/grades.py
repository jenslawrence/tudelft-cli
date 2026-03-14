from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import Grade


def render_grades(grades: list[Grade]) -> None:
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
