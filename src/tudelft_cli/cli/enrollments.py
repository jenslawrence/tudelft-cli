import typer

from tudelft_cli.app.services.enrollments import GetEnrollmentsService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.enrollments import render_enrollments

app = typer.Typer(help="Enrollment overview commands")


@app.command("enrollments", help="Show current course and exam enrollments.")
def enrollments(
    courses: bool = typer.Option(False, "--courses"),
    exams: bool = typer.Option(False, "--exams"),
) -> None:
    try:
        ctx = create_context()
        result = GetEnrollmentsService(ctx.auth, ctx.portal).execute()

        show_courses = courses or not exams
        show_exams = exams or not courses

        render_enrollments(
            result,
            show_courses=show_courses,
            show_exams=show_exams,
        )

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
