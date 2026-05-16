from __future__ import annotations

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import StudentProfile
from tudelft_cli.infra.portal.parsing import as_optional_string


def map_profile_payload(payload: object) -> StudentProfile:
    if not isinstance(payload, dict):
        raise PortalChangedError("Gebruiker endpoint returned an unexpected payload shape.")

    roepnaam = payload.get("roepnaam")
    achternaam = payload.get("achternaam")

    if not isinstance(roepnaam, str) or not isinstance(achternaam, str):
        raise PortalChangedError("Gebruiker payload is missing expected name fields.")

    return StudentProfile(
        name=f"{roepnaam} {achternaam}".strip(),
        student_number=as_optional_string(payload.get("studentnummer")),
        email=as_optional_string(payload.get("e_mailadres")),
    )
