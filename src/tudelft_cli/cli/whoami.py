from enum import Enum
import typer

from tudelft_cli.app.services.profile import GetProfileService
from tudelft_cli.cli.context import create_context
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.profile import render_profile

app = typer.Typer(help="Student profile commands.")


class OutputFormat(str, Enum):
    table = "table"
    pretty = "pretty"


@app.command("whoami", help="Show the currently logged-in student profile.")
def whoami(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
) -> None:
    try:
        ctx = create_context()
        result = GetProfileService(ctx.auth, ctx.portal).execute()
        render_profile(result, pretty=(output == OutputFormat.pretty))

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)
