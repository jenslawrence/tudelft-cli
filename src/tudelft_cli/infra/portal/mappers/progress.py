from __future__ import annotations

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import EcPhaseProgress, EcProgress
from tudelft_cli.infra.portal.parsing import as_optional_string, parse_int, required_string


def map_ec_progress_payload(payload: object) -> EcProgress:
    if not isinstance(payload, dict):
        raise PortalChangedError("Voortgang endpoint returned an unexpected payload shape.")

    items = payload.get("items")
    if not isinstance(items, list):
        raise PortalChangedError("Voortgang payload is missing expected items field.")

    progress_items: list[EcPhaseProgress] = []

    for programme in items:
        if not isinstance(programme, dict):
            continue

        programme_name = required_string(programme, "opleiding_naam")
        exam_phases = programme.get("examenfases")

        if not isinstance(exam_phases, list):
            continue

        for phase in exam_phases:
            if not isinstance(phase, dict):
                continue

            minimum_punten = parse_int(phase.get("minimum_punten"))
            punten_behaald = parse_int(phase.get("punten_behaald"))
            percentage_behaald = parse_int(phase.get("percentage_behaald"))
            overige_behaalde_punten = parse_int(phase.get("overige_behaalde_punten"))

            voldaan = phase.get("voldaan")
            completed: bool | None
            if voldaan == "J":
                completed = True
            elif voldaan == "N":
                completed = False
            else:
                completed = None

            progress_items.append(
                EcPhaseProgress(
                    programme_name=programme_name,
                    faculty=as_optional_string(phase.get("faculteit")),
                    exam_programme_name=as_optional_string(phase.get("examenprogramma_naam")),
                    phase_description=required_string(phase, "examenfase_omschrijving"),
                    earned_ec=punten_behaald,
                    required_ec=minimum_punten,
                    percentage=percentage_behaald,
                    completed=completed,
                    other_earned_ec=overige_behaalde_punten,
                )
            )

    return EcProgress(items=progress_items)
