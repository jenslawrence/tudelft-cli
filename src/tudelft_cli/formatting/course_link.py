import json
from typing import Any

from rich.console import Console

from tudelft_cli.domain.models import CourseLink

console = Console()


def render_course_link(link: CourseLink) -> None:
    console.print(f"[bold]{link.course_code}[/bold]")
    console.print(link.study_guide_url)


def render_course_link_json(link: CourseLink) -> None:
    print(json.dumps(_to_dict(link), indent=2, ensure_ascii=False))


def _to_dict(link: CourseLink) -> dict[str, Any]:
    return {
        "course_code": link.course_code,
        "study_guide_url": link.study_guide_url,
    }