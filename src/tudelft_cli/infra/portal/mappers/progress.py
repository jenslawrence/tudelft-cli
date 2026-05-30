from __future__ import annotations

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import EcPhaseProgress, EcProgress
from tudelft_cli.infra.portal.parsing import (
    as_optional_string,
    optional_int,
    require_dict_item,
    required_list,
    required_str,
)


def map_ec_progress_payload(payload: object) -> EcProgress:
    if not isinstance(payload, dict):
        raise PortalChangedError("Voortgang endpoint returned an unexpected payload shape.")

    items = required_list(payload, "items", "EC progress payload")

    progress_items: list[EcPhaseProgress] = []

    for programme_item in items:
        programme = require_dict_item(programme_item, "EC progress programme")
        programme_name = required_str(programme, "opleiding_naam", "EC progress programme")
        exam_phases = programme.get("examenfases")

        if not isinstance(exam_phases, list):
            continue

        for phase_item in exam_phases:
            phase = require_dict_item(phase_item, "EC progress phase")

            minimum_punten = optional_int(phase, "minimum_punten", "EC progress phase")
            punten_behaald = optional_int(phase, "punten_behaald", "EC progress phase")
            percentage_behaald = optional_int(phase, "percentage_behaald", "EC progress phase")
            overige_behaalde_punten = optional_int(
                phase,
                "overige_behaalde_punten",
                "EC progress phase",
            )

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
                    phase_description=required_str(
                        phase,
                        "examenfase_omschrijving",
                        "EC progress phase",
                    ),
                    earned_ec=punten_behaald,
                    required_ec=minimum_punten,
                    percentage=percentage_behaald,
                    completed=completed,
                    other_earned_ec=overige_behaalde_punten,
                )
            )

    return EcProgress(items=progress_items)
