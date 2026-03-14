from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from tudelft_cli.domain.models import EcProgress


def render_ec_table(progress: EcProgress) -> None:
    console = Console()
    table = Table(title="EC Progress")
    table.add_column("Programme")
    table.add_column("Phase")
    table.add_column("Earned EC")
    table.add_column("Required EC")
    table.add_column("Progress")
    table.add_column("Completed")

    for item in progress.items:
        progress_text = f"{item.percentage}%" if item.percentage is not None else "-"
        earned_text = str(item.earned_ec) if item.earned_ec is not None else "-"
        required_text = str(item.required_ec) if item.required_ec is not None else "-"
        completed_text = (
            "yes" if item.completed else "no" if item.completed is not None else "-"
        )

        table.add_row(
            item.programme_name,
            item.phase_description,
            earned_text,
            required_text,
            progress_text,
            completed_text,
        )

    console.print(table)


def render_ec_json(progress: EcProgress) -> None:
    print(json.dumps(_ec_to_dict(progress), indent=2, ensure_ascii=False))


def _ec_to_dict(progress: EcProgress) -> dict[str, Any]:
    return {
        "items": [
            {
                "programme_name": item.programme_name,
                "faculty": item.faculty,
                "exam_programme_name": item.exam_programme_name,
                "phase_description": item.phase_description,
                "earned_ec": item.earned_ec,
                "required_ec": item.required_ec,
                "percentage": item.percentage,
                "completed": item.completed,
                "other_earned_ec": item.other_earned_ec,
            }
            for item in progress.items
        ]
    }
