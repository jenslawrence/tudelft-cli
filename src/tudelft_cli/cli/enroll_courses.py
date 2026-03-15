from __future__ import annotations

import typer

from tudelft_cli.app.services.enroll_courses import EnrollCoursesService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.enrollments import render_course_enrollments_table
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Course enrollment commands")


@app.command("enroll-course", help="Enroll in a course from the suggested course list.")
def enroll_course(
    course_codes: list[str] = typer.Argument(..., help="One or more course codes to enroll in."),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt."),
) -> None:
    try:
        normalized = [code.strip().upper() for code in course_codes if code.strip()]
        if not yes:
            typer.echo("You are about to enroll in:")
            for code in normalized:
                typer.echo(f"- {code}")
            confirmed = typer.confirm("Proceed?")
            if not confirmed:
                raise typer.Exit(code=0)

        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = EnrollCoursesService(auth_provider, portal).execute(normalized)
        render_course_enrollments_table(result, title="Enrolled courses")

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
