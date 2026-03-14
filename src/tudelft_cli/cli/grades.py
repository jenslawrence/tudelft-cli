from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.grades import GetGradesService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.grades import render_grades_json, render_grades_table
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Grade commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("grades")
def grades(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetGradesService(auth_provider, portal).execute()

        if output == OutputFormat.json:
            render_grades_json(result)
        else:
            render_grades_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
