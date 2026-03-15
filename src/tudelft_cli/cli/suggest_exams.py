from enum import Enum

import typer

from tudelft_cli.app.services.suggest_exams import GetSuggestedExamsService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.suggest_exams import (
    render_suggested_exams_json,
    render_suggested_exams_table,
)
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Suggested exam enrollment commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("suggest-exams", help="Show courses with exam opportunities open for enrollment.")
def suggest_exams(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetSuggestedExamsService(auth_provider, portal).execute()

        if output == OutputFormat.json:
            render_suggested_exams_json(result)
        else:
            render_suggested_exams_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
