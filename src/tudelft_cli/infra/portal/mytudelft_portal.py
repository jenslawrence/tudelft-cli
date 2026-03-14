from __future__ import annotations

import httpx
from typing import Sequence

from tudelft_cli.domain.errors import AuthenticationError, PortalChangedError
from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import AuthSession, Grade, StudentProfile


class MyTUDelftPortal(StudentPortal):
    BASE_URL = "https://my.tudelft.nl/student/osiris"

    def _build_headers(self, session: AuthSession) -> dict[str, str]:
        if not session.access_token:
            raise AuthenticationError("No access token found. Run 'tudelft login' first.")

        return {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {session.access_token}",
            "client_type": "web",
            "Content-Type": "application/json",
            "taal": "NL",
        }

    def get_profile(self, session: AuthSession) -> StudentProfile:
        url = f"{self.BASE_URL}/gebruiker"

        try:
            response = httpx.get(url, headers=self._build_headers(session), timeout=30.0)
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from gebruiker endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Gebruiker endpoint did not return valid JSON.") from exc

        if not isinstance(payload, dict):
            raise PortalChangedError("Gebruiker endpoint returned an unexpected payload shape.")

        roepnaam = payload.get("roepnaam")
        achternaam = payload.get("achternaam")

        if not isinstance(roepnaam, str) or not isinstance(achternaam, str):
            raise PortalChangedError("Gebruiker payload is missing expected name fields.")

        profile = StudentProfile(
            name=f"{roepnaam} {achternaam}".strip(),
            netid=None,
            student_number=self._as_optional_string(payload.get("studentnummer")),
            programme=None,
            faculty=None,
        )

        return profile

    def get_grades(self, session: AuthSession) -> Sequence[Grade]:
        return []

    @staticmethod
    def _as_optional_string(value: object) -> str | None:
        if value is None:
            return None
        return str(value)
