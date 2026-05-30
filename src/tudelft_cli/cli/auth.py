from enum import Enum

import typer

from tudelft_cli.app.services.login import LoginService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.auth_status import render_auth_status

app = typer.Typer(help="Authentication commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


@app.command("login", help="Authenticate with TU Delft via browser login.")
def login() -> None:
    try:
        ctx = create_context()
        session = LoginService(ctx.auth).execute()
        token_type = session.token_type or "unknown"
        typer.echo(f"Login successful ({token_type} token captured)")
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


@app.command("logout", help="Remove the stored TU Delft session.")
def logout() -> None:
    ctx = create_context()
    ctx.auth.logout()
    typer.echo("Logged out")


@app.command("status", help="Show local TU Delft session status without contacting MyTU Delft.")
def status(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        ctx = create_context()
        session = ctx.auth.load_session()
        render_auth_status(session, as_json=(output == OutputFormat.json))
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
