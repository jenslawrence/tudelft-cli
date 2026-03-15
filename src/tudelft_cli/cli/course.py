from enum import Enum
import webbrowser

import typer

from tudelft_cli.app.services.course_link import GetCourseLinkService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.formatting.course_link import render_course_link, render_course_link_json
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Course information commands")


class OutputFormat(str, Enum):
    text = "text"
    json = "json"


@app.command("course", help="Show or open the TU Delft Study Guide page for a course.")
def course(
    course_code: str = typer.Argument(..., help="Course code, e.g. CSE2530"),
    open_: bool = typer.Option(False, "--open", help="Open the Study Guide page in browser."),
    output: OutputFormat = typer.Option(OutputFormat.text, "--output", "-o"),
) -> None:
    try:
        portal = MyTUDelftPortal()
        link = GetCourseLinkService(portal).execute(course_code)

        if output == OutputFormat.json:
            render_course_link_json(link)
        else:
            render_course_link(link)

        if open_:
            opened = webbrowser.open(link.study_guide_url)
            if not opened:
                typer.echo("Warning: Could not open browser automatically.")

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)