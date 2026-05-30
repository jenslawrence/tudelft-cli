import typer

from tudelft_cli.app.services.login import LoginService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError

app = typer.Typer(help="Authentication commands")


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
