from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.ec import GetEcProgressService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.ec import render_ec
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="EC progress commands.")


class OutputFormat(str, Enum):
    table = "table"
    pretty = "pretty"
    json = "json"


@app.command("ec", help="Show EC progress per programme and phase.")
def ec(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetEcProgressService(auth_provider, portal).execute()

        render_ec(
            result,
            pretty=(output == OutputFormat.pretty),
            as_json=(output == OutputFormat.json),
        )

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)