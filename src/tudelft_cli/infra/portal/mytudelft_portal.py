from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

import httpx

from tudelft_cli.domain.errors import AuthenticationError, PortalChangedError
from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import AuthSession, EcPhaseProgress, EcProgress, Grade, StudentProfile


class MyTUDelftPortal(StudentPortal):
    BASE_URL = "https://my.tudelft.nl/student/osiris"
    RESULTS_PAGE_SIZE = 100

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

        return StudentProfile(
            name=f"{roepnaam} {achternaam}".strip(),
            netid=None,
            student_number=self._as_optional_string(payload.get("studentnummer")),
            programme=None,
            faculty=None,
        )

    def get_grades(self, session: AuthSession) -> Sequence[Grade]:
        headers = self._build_headers(session)
        url = f"{self.BASE_URL}/student/resultaten"

        offset = 0
        grades: list[Grade] = []

        while True:
            params = {
                "limit": self.RESULTS_PAGE_SIZE,
                "offset": offset,
            }

            try:
                response = httpx.get(url, headers=headers, params=params, timeout=30.0)
            except httpx.HTTPError as exc:
                raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

            if response.status_code == 401:
                raise AuthenticationError(
                    "Stored session is no longer valid. Run 'tudelft login' again."
                )

            if response.status_code != 200:
                raise PortalChangedError(
                    f"Unexpected response from resultaten endpoint: {response.status_code}"
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise PortalChangedError("Resultaten endpoint did not return valid JSON.") from exc

            if not isinstance(payload, dict):
                raise PortalChangedError("Resultaten endpoint returned an unexpected payload shape.")

            items = payload.get("items")
            has_more = payload.get("hasMore")

            if not isinstance(items, list) or not isinstance(has_more, bool):
                raise PortalChangedError("Resultaten payload is missing expected pagination fields.")

            for item in items:
                if not isinstance(item, dict):
                    continue
                grades.append(self._map_grade(item))

            if not has_more:
                break

            offset += self.RESULTS_PAGE_SIZE

        return grades

    def _map_grade(self, item: dict[str, Any]) -> Grade:
        course_code = self._required_string(item, "cursus")
        course_name = self._required_string(item, "cursus_korte_naam")
        component = self._required_string(item, "toets_omschrijving")
        value = self._required_string(item, "resultaat")

        voldoende = item.get("voldoende")
        passed: bool | None
        if voldoende == "J":
            passed = True
        elif voldoende == "N":
            passed = False
        else:
            passed = None

        published_at = self._parse_datetime(item.get("mutatiedatum"))

        return Grade(
            course_code=course_code,
            course_name=course_name,
            component=component,
            value=value,
            passed=passed,
            published_at=published_at,
        )

    def get_ec_progress(self, session: AuthSession) -> EcProgress:
        url = f"{self.BASE_URL}/student/voortgang/per_opleiding/"

        try:
            response = httpx.get(url, headers=self._build_headers(session), timeout=30.0)
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from voortgang endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Voortgang endpoint did not return valid JSON.") from exc

        if not isinstance(payload, dict):
            raise PortalChangedError("Voortgang endpoint returned an unexpected payload shape.")

        items = payload.get("items")
        if not isinstance(items, list):
            raise PortalChangedError("Voortgang payload is missing expected items field.")

        progress_items: list[EcPhaseProgress] = []

        for programme in items:
            if not isinstance(programme, dict):
                continue

            programme_name = self._required_string(programme, "opleiding_naam")
            exam_phases = programme.get("examenfases")

            if not isinstance(exam_phases, list):
                continue

            for phase in exam_phases:
                if not isinstance(phase, dict):
                    continue

                minimum_punten = self._parse_int(phase.get("minimum_punten"))
                punten_behaald = self._parse_int(phase.get("punten_behaald"))
                percentage_behaald = self._parse_int(phase.get("percentage_behaald"))
                overige_behaalde_punten = self._parse_int(phase.get("overige_behaalde_punten"))

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
                        faculty=self._as_optional_string(phase.get("faculteit")),
                        exam_programme_name=self._as_optional_string(
                            phase.get("examenprogramma_naam")
                        ),
                        phase_description=self._required_string(phase, "examenfase_omschrijving"),
                        earned_ec=punten_behaald,
                        required_ec=minimum_punten,
                        percentage=percentage_behaald,
                        completed=completed,
                        other_earned_ec=overige_behaalde_punten,
                    )
                )

        return EcProgress(items=progress_items)

    @staticmethod
    def _required_string(item: dict[str, Any], key: str) -> str:
        value = item.get(key)
        if not isinstance(value, str):
            raise PortalChangedError(f"Result item is missing expected field: {key}")
        return value

    @staticmethod
    def _as_optional_string(value: object) -> str | None:
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _parse_int(value: object) -> int | None:
        if value is None or value == "":
            return None
        try:
            return int(str(value))
        except ValueError:
            return None
