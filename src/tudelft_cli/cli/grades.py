import typer

from tudelft_cli.app.services.grades import GetGradesService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.grades import render_grades
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Grade commands")


@app.command("grades")
def grades() -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = GetGradesService(auth_provider, portal).execute()
        render_grades(result)
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
