from __future__ import annotations

from enum import Enum

import typer

from tudelft_cli.app.services.grades import GetGradesService
from tudelft_cli.domain.errors import TUDelftCliError
from tudelft_cli.domain.models import Grade
from tudelft_cli.formatting.grades import render_grades_json, render_grades_table
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal

app = typer.Typer(help="Grade commands")


class OutputFormat(str, Enum):
    table = "table"
    json = "json"


FINAL_COMPONENT_NAMES = {
    "final",
    "final grade",
}


@app.command("grades", help="Show recorded grades from MyTU Delft.")
def grades(
    output: OutputFormat = typer.Option(OutputFormat.table, "--output", "-o"),
    final_only: bool = typer.Option(False, "--final-only", help="Show only final results."),
) -> None:
    try:
        auth_provider = BrowserAuthProvider(SessionStore())
        portal = MyTUDelftPortal()
        result = list(GetGradesService(auth_provider, portal).execute())

        if final_only:
            result = [grade for grade in result if _is_final_grade(grade)]

        if output == OutputFormat.json:
            render_grades_json(result)
        else:
            render_grades_table(result)

    except TUDelftCliError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=1)


def _is_final_grade(grade: Grade) -> bool:
    return grade.component.strip().lower() in FINAL_COMPONENT_NAMES
