from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.suggest_courses import GetSuggestedCoursesService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.suggest_courses import (
    render_suggested_courses_json,
    render_suggested_courses_table,
)
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Suggested course enrollment commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("suggest-courses")
def suggest_courses(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetSuggestedCoursesService(auth_provider, portal).execute()

        if output == OutputFormat.json:
            render_suggested_courses_json(result)
        else:
            render_suggested_courses_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
