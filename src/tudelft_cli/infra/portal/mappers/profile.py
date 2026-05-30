from __future__ import annotations

from tudelft_cli.domain.errors import PortalChangedError
from tudelft_cli.domain.models import StudentProfile
from tudelft_cli.infra.portal.parsing import as_optional_string, required_str


def map_profile_payload(payload: object) -> StudentProfile:
    if not isinstance(payload, dict):
        raise PortalChangedError("Gebruiker endpoint returned an unexpected payload shape.")

    roepnaam = required_str(payload, "roepnaam", "profile")
    achternaam = required_str(payload, "achternaam", "profile")

    return StudentProfile(
        name=f"{roepnaam} {achternaam}".strip(),
        student_number=as_optional_string(payload.get("studentnummer")),
        email=as_optional_string(payload.get("e_mailadres")),
    )
