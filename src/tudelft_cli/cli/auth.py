import typer

from tudelft_cli.app.services.login import LoginService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login() -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        session = LoginService(auth_provider).execute()
        token_type = session.token_type or "unknown"
        typer.echo(f"Login successful ({token_type} token captured)")
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


@app.command("logout")
def logout() -> None:
    auth_provider = BrowserAuthProvider(SessionStore())
    auth_provider.logout()
    typer.echo("Logged out")
