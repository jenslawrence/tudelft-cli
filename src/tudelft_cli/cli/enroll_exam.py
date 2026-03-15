from __future__ import annotations

import typer
import questionary
from questionary import Choice
from questionary import Style

from tudelft_cli.app.services.enroll_exam import EnrollExamService
from tudelft_cli.app.services.exam_opportunities import GetExamOpportunitiesService
from tudelft_cli.domain.errors import TUDelftCliError, ValidationError
from tudelft_cli.formatting.enrollments import render_exam_enrollments_table
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Exam enrollment commands")

EXAM_SELECT_STYLE = Style(
    [
        ("qmark", "fg:#00A6D6 bold"),
        ("question", "bold"),
        ("pointer", "fg:#00A6D6 bold"),
        ("highlighted", "fg:#00A6D6 bold"),
        ("selected", "fg:#00A6D6"),
        ("answer", "fg:#00A6D6 bold"),
    ]
)

def _format_exam_opportunity_label(exam) -> str:
    exam_name = getattr(exam, "test_description", None) or "-"
    block = getattr(exam, "block", None) or "-"
    exam_dt = getattr(exam, "exam_datetime", None)
    exam_date = exam_dt.date().isoformat() if exam_dt else "-"
    start_time = getattr(exam, "start_time", None) or ""
    end_time = getattr(exam, "end_time", None) or ""
    time_range = f"{start_time}-{end_time}" if start_time and end_time else "-"
    attempt = getattr(exam, "opportunity", None)

    parts = [
        str(exam_name),
        f"Block {block}",
        str(exam_date),
        str(time_range),
    ]
    if attempt is not None:
        parts.append(f"Attempt {attempt}")

    return " | ".join(parts)

def _select_exam_opportunity(course, opportunities: list) -> int:
    if not opportunities:
        raise ValidationError(f"No available exam opportunities found for {course.course_code}")

    if len(opportunities) == 1:
        return 1

    choices = [
        Choice(
            title=f"{index}. {_format_exam_opportunity_label(opportunity)}",
            value=index,
        )
        for index, opportunity in enumerate(opportunities, start=1)
    ]

    choices.append(
        Choice(
            title=f"{len(opportunities) + 1}. Cancel (Esc)",
            value="cancel",
        )
    )

    selected = questionary.select(
        f"Select exam opportunity for {course.course_code} ({course.course_name})",
        choices=choices,
        style=EXAM_SELECT_STYLE,
        use_shortcuts=False,
        use_indicator=False,
        qmark="",
        pointer="❯",
        instruction="",
    ).ask()

    if selected is None or selected == "cancel":
        raise typer.Exit(code=0)

    return int(selected)

@app.command("enroll-exam", help="Enroll in an exam opportunity for a course.")
def enroll_exam(
    course_code: str = typer.Argument(..., help="Course code to enroll exam(s) for."),
    select: int | None = typer.Option(
        None,
        "--select",
        help="Exam opportunity number. If omitted and multiple opportunities exist, an interactive selector opens.",
    ),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt."),
) -> None:
    try:
        normalized = course_code.strip().upper()

        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()

        course, opportunities = GetExamOpportunitiesService(auth_provider, portal).execute(normalized)

        chosen = select
        if chosen is None:
            chosen = _select_exam_opportunity(course, opportunities)

        selected_opportunity = opportunities[chosen - 1]
        selected_label = _format_exam_opportunity_label(selected_opportunity)

        if not yes:
            typer.echo(f"You are about to enroll for an exam of: {normalized}")
            typer.echo(f"Selected opportunity: {selected_label}")
            confirmed = typer.confirm("Proceed?")
            if not confirmed:
                raise typer.Exit(code=0)

        result = EnrollExamService(auth_provider, portal).execute(normalized, selection=chosen)
        render_exam_enrollments_table(result, title="Enrolled exam")

    except IndexError:
        typer.echo("Error: Selected exam opportunity number is out of range.")
        raise typer.Exit(code=1)
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
