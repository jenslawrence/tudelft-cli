import typer

from tudelft_cli.app.services.login import LoginService
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login() -> None:
    auth_provider = BrowserAuthProvider(SessionStore())
    session = LoginService(auth_provider).execute()
    typer.echo(f"Logged in as {session.netid or 'unknown user'}")


@app.command("logout")
def logout() -> None:
    auth_provider = BrowserAuthProvider(SessionStore())
    auth_provider.logout()
    typer.echo("Logged out")
