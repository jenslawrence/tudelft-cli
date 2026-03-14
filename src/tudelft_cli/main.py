from tudelft_cli.cli.auth import app as auth_app
from tudelft_cli.cli.grades import app as grades_app
from tudelft_cli.cli.root import app


@app.command("whoami")
def whoami() -> None:
    from tudelft_cli.app.services.profile import GetProfileService
    from tudelft_cli.domain.errors import TUDelftCliError
    from tudelft_cli.formatting.profile import render_profile
    from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
    from tudelft_cli.infra.auth.session_store import SessionStore
    from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal
    import typer

    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        profile = GetProfileService(auth_provider, portal).execute()
        render_profile(profile)
    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


app.add_typer(auth_app)
app.add_typer(grades_app)


def main() -> None:
    app()

if __name__ == "__main__":
    main()
