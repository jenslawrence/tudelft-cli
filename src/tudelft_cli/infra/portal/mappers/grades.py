from __future__ import annotations

from typing import Any

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import Grade
from tudelft_cli.infra.portal.parsing import parse_datetime, required_string


def map_grades_page(payload: object, *, final_only: bool) -> tuple[list[Grade], bool]:
    if not isinstance(payload, dict):
        raise PortalChangedError("Resultaten endpoint returned an unexpected payload shape.")

    items = payload.get("items")
    has_more = payload.get("hasMore")

    if not isinstance(items, list) or not isinstance(has_more, bool):
        raise PortalChangedError("Resultaten payload is missing expected pagination fields.")

    grades: list[Grade] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        grade = map_grade(item)

        if final_only:
            component = grade.component.strip().lower()
            if component not in {"final", "final grade"}:
                continue

        grades.append(grade)

    return grades, has_more


def map_grade(item: dict[str, Any]) -> Grade:
    course_code = required_string(item, "cursus")
    course_name = required_string(item, "cursus_korte_naam")
    component = required_string(item, "toets_omschrijving")
    value = required_string(item, "resultaat")

    voldoende = item.get("voldoende")
    passed: bool | None
    if voldoende == "J":
        passed = True
    elif voldoende == "N":
        passed = False
    else:
        passed = None

    published_at = parse_datetime(item.get("mutatiedatum"))

    return Grade(
        course_code=course_code,
        course_name=course_name,
        component=component,
        value=value,
        passed=passed,
        published_at=published_at,
    )
