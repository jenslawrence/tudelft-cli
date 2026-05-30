from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.suggest_courses import GetSuggestedCoursesService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.suggest_courses import (
    render_suggested_courses_json,
    render_suggested_courses_table,
)

app = typer.Typer(help="Suggested course enrollment commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("suggest-courses", help="Show courses currently open for enrollment in your programme.")
def suggest_courses(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        ctx = create_context()
        result = GetSuggestedCoursesService(ctx.auth, ctx.portal).execute()

        if output == OutputFormat.json:
            render_suggested_courses_json(result)
        else:
            render_suggested_courses_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
