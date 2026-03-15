from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import CourseEnrollment

console = Console()


def render_course_enrollments_table(
    courses: list[CourseEnrollment],
    title: str = "Course enrollments",
) -> None:
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


def render_exam_enrollments_table(exams: list, title: str = "Exam enrollments") -> None:
    table = Table(title=title)
    table.add_column("Code")
    table.add_column("Course")
    table.add_column("Exam")
    table.add_column("Date")
    table.add_column("Time")
    table.add_column("Attempt")
    table.add_column("Can unenroll")

    for exam in exams:
        exam_name = getattr(exam, "test_description", None) or "-"
        exam_dt = getattr(exam, "exam_datetime", None)
        exam_date = exam_dt.date().isoformat() if exam_dt else "-"
        start_time = getattr(exam, "start_time", None) or ""
        end_time = getattr(exam, "end_time", None) or ""
        time_range = f"{start_time}-{end_time}" if start_time and end_time else "-"
        attempt = getattr(exam, "opportunity", None)
        can_unenroll = getattr(exam, "can_unenroll", None)

        table.add_row(
            exam.course_code,
            exam.course_name,
            exam_name,
            exam_date,
            time_range,
            str(attempt) if attempt is not None else "-",
            "yes" if can_unenroll else "no" if can_unenroll is not None else "-",
        )

    console.print(table)


def render_enrollments(
    data: dict,
    show_courses: bool = True,
    show_exams: bool = True,
) -> None:
    if show_courses:
        courses = data.get("courses", [])
        console.print()
        if courses:
            render_course_enrollments_table(courses, title="Courses")
        else:
            console.print("[bold]Courses[/bold]")
            console.print("No enrolled courses.")

    if show_exams:
        exams = data.get("exams", [])
        console.print()
        if exams:
            render_exam_enrollments_table(exams, title="Exams")
        else:
            console.print("[bold]Exams[/bold]")
            console.print("No enrolled exams.")
