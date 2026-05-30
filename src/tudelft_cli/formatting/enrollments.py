import json
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import CourseEnrollment, ExamEnrollment

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
    as_json: bool = False,
) -> None:
    if as_json:
        render_enrollments_json(
            data,
            show_courses=show_courses,
            show_exams=show_exams,
        )
        return

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


def render_enrollments_json(
    data: dict,
    show_courses: bool = True,
    show_exams: bool = True,
) -> None:
    print(
        json.dumps(
            _enrollments_to_dict(data, show_courses=show_courses, show_exams=show_exams),
            indent=2,
            ensure_ascii=False,
        )
    )


def _enrollments_to_dict(
    data: dict,
    show_courses: bool = True,
    show_exams: bool = True,
) -> dict[str, Any]:
    courses = data.get("courses", []) if show_courses else []
    exams = data.get("exams", []) if show_exams else []

    return {
        "course_enrollments": [_course_to_dict(course) for course in courses],
        "exam_enrollments": [_exam_to_dict(exam) for exam in exams],
    }


def _course_to_dict(course: CourseEnrollment) -> dict[str, Any]:
    return {
        "course_offering_id": course.course_offering_id,
        "course_id": course.course_id,
        "course_code": course.course_code,
        "academic_year": course.academic_year,
        "block": course.block,
        "period_description": course.period_description,
        "period_date_range": course.period_date_range,
        "course_name": course.course_name,
        "ec": course.ec,
        "ec_unit": course.ec_unit,
        "programme_part": course.programme_part,
        "can_unenroll": course.can_unenroll,
        "is_new": course.is_new,
        "is_historical": course.is_historical,
    }


def _exam_to_dict(exam: ExamEnrollment) -> dict[str, Any]:
    return {
        "exam_offering_id": exam.exam_offering_id,
        "course_id": exam.course_id,
        "course_code": exam.course_code,
        "academic_year": exam.academic_year,
        "course_name": exam.course_name,
        "programme_part": exam.programme_part,
        "test_code": exam.test_code,
        "test_description": exam.test_description,
        "block": exam.block,
        "period_description": exam.period_description,
        "opportunity": exam.opportunity,
        "exam_datetime": exam.exam_datetime.isoformat() if exam.exam_datetime else None,
        "day": exam.day,
        "start_time": exam.start_time,
        "end_time": exam.end_time,
        "can_unenroll": exam.can_unenroll,
        "is_new": exam.is_new,
        "result": exam.result,
        "is_historical": exam.is_historical,
    }
