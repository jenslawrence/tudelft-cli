from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.grades import GetGradesService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.grades import render_grades

app = typer.Typer(help="Grade commands.")


class OutputFormat(str, Enum):
    table = "table"
    pretty = "pretty"
    json = "json"


@app.command("grades", help="Show recorded grades from MyTU Delft.")
def grades(
    final_only: bool = typer.Option(False, "--final-only", help="Show final results only."),
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        ctx = create_context()
        result = GetGradesService(ctx.auth, ctx.portal).execute(final_only=final_only)

        render_grades(
            result,
            pretty=(output == OutputFormat.pretty),
            as_json=(output == OutputFormat.json),
        )

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
