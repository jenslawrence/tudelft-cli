import typer

from tudelft_cli.app.services.profile import GetProfileService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.profile import render_profile
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Student profile commands.")


@app.command("whoami", help="Show the currently logged-in student profile.")
def whoami(
    pretty: bool = typer.Option(False, "--pretty", help="Use richer visual output."),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetProfileService(auth_provider, portal).execute()
        render_profile(result, pretty=pretty)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)