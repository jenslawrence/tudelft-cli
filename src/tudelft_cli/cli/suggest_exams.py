from enum import Enum

import typer

from tudelft_cli.app.services.suggest_exams import GetSuggestedExamsService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.suggest_exams import (
    render_suggested_exams_json,
    render_suggested_exams_table,
)

app = typer.Typer(help="Suggested exam enrollment commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("suggest-exams", help="Show courses with exam opportunities open for enrollment.")
def suggest_exams(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        ctx = create_context()
        result = GetSuggestedExamsService(ctx.auth, ctx.portal).execute()

        if output == OutputFormat.json:
            render_suggested_exams_json(result)
        else:
            render_suggested_exams_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
