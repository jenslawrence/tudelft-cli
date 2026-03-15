import typer

from tudelft_cli.app.services.profile import GetProfileService
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.formatting.profile import render_profile

app = typer.Typer(help="Student profile commands")


@app.command("whoami", help="Show current TU Delft student profile.")
def whoami():
    auth_provider = BrowserAuthProvider(SessionStore())
    portal = MyTUDelftPortal()

    result = GetProfileService(auth_provider, portal).execute()
    render_profile(result)