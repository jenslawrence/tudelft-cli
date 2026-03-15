from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

import httpx

from tudelft_cli.domain.errors import AuthenticationError, PortalChangedError, ValidationError
from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import (
    AuthSession,
    CourseEnrollment,
    ExamEnrollment,
    EcPhaseProgress,
    EcProgress,
    Grade,
    StudentProfile,
    SuggestedCourse,
    SuggestedExamCourse,
    ExamOpportunity,
)

class MyTUDelftPortal(StudentPortal):
    BASE_URL = "https://my.tudelft.nl/student/osiris"
    RESULTS_PAGE_SIZE = 100
    COURSE_SUGGESTIONS_URL = (
    f"{BASE_URL}/student/cursussen_voor_cursusinschrijving/te_volgen_onderwijs/open_voor_inschrijving/"
)
    COURSE_ENROLLMENTS_URL = f"{BASE_URL}/student/inschrijvingen/cursussen"
    EXAM_SUGGESTIONS_URL = (
        f"{BASE_URL}/student/cursussen_voor_toetsinschrijving/te_volgen_onderwijs/open_voor_inschrijving/"
    )
    EXAM_OPPORTUNITIES_URL = f"{BASE_URL}/student/cursussen_voor_toetsinschrijving"
    EXAM_ENROLLMENTS_URL = f"{BASE_URL}/student/inschrijvingen/toetsen/"

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

    def get_suggested_courses(self, session: AuthSession) -> list[SuggestedCourse]:
        try:
            response = httpx.get(
                self.COURSE_SUGGESTIONS_URL,
                headers=self._build_headers(session),
                params={"limit": 9999},
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from suggested courses endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Suggested courses endpoint did not return valid JSON.") from exc

        items = payload.get("items")
        if not isinstance(items, list):
            raise PortalChangedError("Suggested courses payload is missing expected items.")

        suggestions: list[SuggestedCourse] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            suggestions.append(self._map_suggested_course(item))

        return suggestions
    
    def get_course_enrollments(self, session: AuthSession) -> list[CourseEnrollment]:
        try:
            response = httpx.get(
                self.COURSE_ENROLLMENTS_URL,
                headers=self._build_headers(session),
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from course enrollments endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Course enrollments endpoint did not return valid JSON.") from exc

        items = payload.get("items")
        if not isinstance(items, list):
            raise PortalChangedError("Course enrollments payload is missing expected items.")

        enrollments: list[CourseEnrollment] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            enrollments.append(self._map_course_enrollment(item))

        return enrollments

    def get_exam_enrollments(self, session: AuthSession) -> list[ExamEnrollment]:
        try:
            response = httpx.get(
                self.EXAM_ENROLLMENTS_URL,
                headers=self._build_headers(session),
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from exam enrollments endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Exam enrollments endpoint did not return valid JSON.") from exc

        items = payload.get("items")
        if not isinstance(items, list):
            raise PortalChangedError("Exam enrollments payload is missing expected items.")

        exams: list[ExamEnrollment] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            exams.append(self._map_exam_enrollment(item))

        return exams
    
    def get_suggested_exam_courses(self, session: AuthSession) -> list[SuggestedExamCourse]:
        try:
            response = httpx.get(
                self.EXAM_SUGGESTIONS_URL,
                headers=self._build_headers(session),
                params={"limit": 9999},
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from suggested exams endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Suggested exams endpoint did not return valid JSON.") from exc

        items = payload.get("items")
        if not isinstance(items, list):
            raise PortalChangedError("Suggested exams payload is missing expected items.")

        return [self._map_suggested_exam_course(item) for item in items if isinstance(item, dict)]

    def get_exam_opportunities(
        self,
        session: AuthSession,
        course_code: str,
    ) -> tuple[SuggestedExamCourse, list[ExamOpportunity]]:
        suggestions = self.get_suggested_exam_courses(session)
        selected_course = next(
            (course for course in suggestions if course.course_code.upper() == course_code.upper()),
            None,
        )
        if selected_course is None:
            raise ValidationError(f"Course not found in suggested exams: {course_code}")

        _, opportunities, _ = self._get_exam_opportunities(session, selected_course.course_id)
        return selected_course, opportunities

    def _get_exam_opportunities(
        self,
        session: AuthSession,
        course_id: int,
    ) -> tuple[SuggestedExamCourse, list[ExamOpportunity], list[dict[str, Any]]]:
        try:
            response = httpx.get(
                f"{self.EXAM_OPPORTUNITIES_URL}/{course_id}",
                headers=self._build_headers(session),
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response from exam opportunities endpoint: {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalChangedError("Exam opportunities endpoint did not return valid JSON.") from exc

        toetsen = payload.get("toetsen")
        if not isinstance(toetsen, list):
            raise PortalChangedError("Exam opportunities payload is missing expected toetsen list.")

        course = SuggestedExamCourse(
            course_id=int(payload["id_cursus"]),
            course_code=self._required_string(payload, "cursus"),
            academic_year=self._parse_int(payload.get("collegejaar")),
            course_name=self._required_string(payload, "cursus_korte_naam"),
            ec=self._parse_float(payload.get("punten")),
            ec_unit=self._as_optional_string(payload.get("punteneenheid")),
            faculty=self._as_optional_string(payload.get("faculteit_naam")),
            category=self._as_optional_string(payload.get("categorie_omschrijving")),
            course_type=self._as_optional_string(payload.get("cursustype_omschrijving")),
            programme_part=self._as_optional_string(payload.get("onderdeel_van")),
        )

        opportunities = [
            self._map_exam_opportunity(item) for item in toetsen if isinstance(item, dict)
        ]
        raw_items = [item for item in toetsen if isinstance(item, dict)]
        return course, opportunities, raw_items

    def enroll_courses(self, session: AuthSession, course_codes: list[str]) -> list[CourseEnrollment]:
        suggestions = self.get_suggested_courses(session)
        by_code = {course.course_code.upper(): course for course in suggestions}

        missing = [code for code in course_codes if code not in by_code]
        if missing:
            raise ValidationError(
                f"Course(s) not found in suggested courses: {', '.join(missing)}"
            )

        headers = self._build_headers(session)

        for code in course_codes:
            course = by_code[code]
            url = f"{self.COURSE_ENROLLMENTS_URL}/{course.course_offering_id}"
            body = self._build_course_enrollment_payload(course)

            try:
                response = httpx.put(url, headers=headers, json=body, timeout=30.0)
            except httpx.HTTPError as exc:
                raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

            if response.status_code == 401:
                raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

            if response.status_code != 200:
                raise PortalChangedError(
                    f"Unexpected response while enrolling in {code}: {response.status_code}"
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise PortalChangedError(
                    f"Enrollment response for {code} did not return valid JSON."
                ) from exc

            statusmeldingen = payload.get("statusmeldingen")
            if not isinstance(statusmeldingen, list):
                raise PortalChangedError(
                    f"Enrollment response for {code} is missing statusmeldingen."
                )

        enrollments = self.get_course_enrollments(session)
        enrolled_codes = {item.course_code.upper() for item in enrollments}
        not_verified = [code for code in course_codes if code not in enrolled_codes]
        if not_verified:
            raise PortalChangedError(
                f"Enrollment could not be verified for: {', '.join(not_verified)}"
            )

        return [item for item in enrollments if item.course_code.upper() in set(course_codes)]

    def enroll_exam(
        self,
        session: AuthSession,
        course_code: str,
        selection: int | None = None,
    ) -> list[ExamEnrollment]:
        suggestions = self.get_suggested_exam_courses(session)
        selected_course = next(
            (course for course in suggestions if course.course_code.upper() == course_code.upper()),
            None,
        )
        if selected_course is None:
            raise ValidationError(f"Course not found in suggested exams: {course_code}")

        _, opportunities, raw_items = self._get_exam_opportunities(session, selected_course.course_id)

        if not opportunities:
            raise ValidationError(f"No available exam opportunities found for {course_code}")

        if selection is None:
            if len(opportunities) != 1:
                raise ValidationError(
                    f"{course_code} has multiple exam opportunities. Provide --select <number>."
                )
            selected_index = 0
        else:
            selected_index = selection - 1
            if selected_index < 0 or selected_index >= len(opportunities):
                raise ValidationError("Selected exam opportunity number is out of range.")

        raw_exam = dict(raw_items[selected_index])
        raw_exam["voorzieningen"] = raw_exam.get("voorzieningen", [])
        raw_exam["renderIndex"] = 0

        if raw_exam.get("tijd_vanaf") is not None:
            raw_exam["tijd_vanaf"] = self._format_time_decimal(raw_exam["tijd_vanaf"])
        if raw_exam.get("tijd_tm") is not None:
            raw_exam["tijd_tm"] = self._format_time_decimal(raw_exam["tijd_tm"])

        payload = {"toetsen": [raw_exam]}

        try:
            response = httpx.post(
                self.EXAM_ENROLLMENTS_URL,
                headers=self._build_headers(session),
                json=payload,
                timeout=30.0,
            )
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(
                f"Unexpected response while enrolling exam for {course_code}: {response.status_code}"
            )

        enrollments = self.get_exam_enrollments(session)
        selected_offering_id = opportunities[selected_index].exam_offering_id
        matching = [item for item in enrollments if item.exam_offering_id == selected_offering_id]

        if not matching:
            raise PortalChangedError(f"Exam enrollment could not be verified for {course_code}")

        return matching

    def _map_suggested_course(self, item: dict[str, Any]) -> SuggestedCourse:
        return SuggestedCourse(
            course_offering_id=int(item["id_cursus_blok"]),
            course_id=int(item["id_cursus"]),
            course_code=self._required_string(item, "cursus"),
            academic_year=self._as_optional_string(item.get("collegejaar")),
            block=self._as_optional_string(item.get("blok")),
            period_description=self._as_optional_string(item.get("periode_omschrijving")),
            period_date_range=None,
            course_name=self._required_string(item, "cursus_korte_naam"),
            faculty=self._as_optional_string(item.get("faculteit_naam")),
            category=self._as_optional_string(item.get("categorie_omschrijving")),
            ec=self._as_optional_string(item.get("punten")),
            ec_unit=self._as_optional_string(item.get("punteneenheid")),
            availability=True,
            waiting_list=None,
            coordinating_unit=self._as_optional_string(item.get("coordinerend_onderdeel_oms")),
            course_type=self._as_optional_string(item.get("cursustype_omschrijving")),
            teaching_form_description=self._as_optional_string(item.get("onderwijsvorm_omschrijving")),
            course_note=self._as_optional_string(item.get("opmerking_cursus")),
            course_block_note=self._as_optional_string(item.get("opmerking_cursus_blok")),
            programme_part=self._as_optional_string(item.get("onderdeel_van")),
        )

    def _map_suggested_exam_course(self, item: dict[str, Any]) -> SuggestedExamCourse:
        return SuggestedExamCourse(
            course_id=int(item["id_cursus"]),
            course_code=self._required_string(item, "cursus"),
            academic_year=self._parse_int(item.get("collegejaar")),
            course_name=self._required_string(item, "cursus_korte_naam"),
            ec=self._parse_float(item.get("punten")),
            ec_unit=self._as_optional_string(item.get("punteneenheid")),
            faculty=self._as_optional_string(item.get("faculteit_naam")),
            category=self._as_optional_string(item.get("categorie_omschrijving")),
            course_type=self._as_optional_string(item.get("cursustype_omschrijving")),
            programme_part=self._as_optional_string(item.get("onderdeel_van")),
        )

    def _map_exam_opportunity(self, item: dict[str, Any]) -> ExamOpportunity:
        return ExamOpportunity(
            course_id=int(item["id_cursus"]),
            exam_offering_id=int(item["id_toets_gelegenheid"]),
            test_code=self._as_optional_string(item.get("toets")),
            test_description=self._as_optional_string(item.get("toets_omschrijving")),
            test_type_description=self._as_optional_string(item.get("toetsvorm_omschrijving")),
            block=self._as_optional_string(item.get("blok")),
            period_description=self._as_optional_string(item.get("periode_omschrijving")),
            opportunity=self._parse_int(item.get("gelegenheid")),
            exam_datetime=self._parse_datetime(item.get("toetsdatum")),
            day=self._as_optional_string(item.get("dag")),
            start_time=self._format_time_decimal(item.get("tijd_vanaf")),
            end_time=self._format_time_decimal(item.get("tijd_tm")),
        )

    def _map_course_enrollment(self, item: dict[str, Any]) -> CourseEnrollment:
        return CourseEnrollment(
            course_offering_id=int(item["id_cursus_blok"]),
            course_id=int(item["id_cursus"]),
            course_code=self._required_string(item, "cursus"),
            academic_year=self._parse_int(item.get("collegejaar")),
            block=self._as_optional_string(item.get("blok")),
            period_description=self._as_optional_string(item.get("periode_omschrijving")),
            period_date_range=self._as_optional_string(item.get("periode_start_einddatum")),
            course_name=self._required_string(item, "cursus_korte_naam"),
            ec=self._parse_float(item.get("punten")),
            ec_unit=self._as_optional_string(item.get("punteneenheid")),
            programme_part=self._as_optional_string(item.get("onderdeel_van")),
            can_unenroll=self._parse_bool_jn(item.get("mag_uitschrijven")),
            is_new=self._parse_bool_jn(item.get("nieuw")),
            is_historical=self._parse_bool_jn(item.get("historie")),
        )

    def _map_exam_enrollment(self, item: dict[str, Any]) -> ExamEnrollment:
        return ExamEnrollment(
            exam_offering_id=int(item["id_toets_gelegenheid"]),
            course_id=int(item["id_cursus"]),
            course_code=self._required_string(item, "cursus"),
            academic_year=self._parse_int(item.get("collegejaar")),
            course_name=self._required_string(item, "cursus_korte_naam"),
            programme_part=self._as_optional_string(item.get("onderdeel_van")),
            test_code=self._as_optional_string(item.get("toets")),
            test_description=self._as_optional_string(item.get("toets_omschrijving")),
            block=self._as_optional_string(item.get("blok")),
            period_description=self._as_optional_string(item.get("periode_omschrijving")),
            opportunity=self._parse_int(item.get("gelegenheid")),
            exam_datetime=self._parse_datetime(item.get("toetsdatum")),
            day=self._as_optional_string(item.get("dag")),
            start_time=self._format_time_decimal(item.get("tijd_vanaf")),
            end_time=self._format_time_decimal(item.get("tijd_tm")),
            can_unenroll=self._parse_bool_jn(item.get("mag_uitschrijven")),
            is_new=self._parse_bool_jn(item.get("nieuw")),
            result=self._as_optional_string(item.get("resultaat")),
            is_historical=self._parse_bool_jn(item.get("historie")),
        )

    def _build_course_enrollment_payload(self, course: SuggestedCourse) -> dict[str, Any]:
        return {
            "toets_voorzieningen": [],
            "toetsen": [],
            "werkvorm_groepen": [],
            "werkvormgroepen_per_werkvorm": [],
            "werkvormen": [],
            "werkvormen_niet_beschikbaar": [],
            "werkvorm_voorzieningen": [],
            "blokken": [],
            "blokken_nested": [],
            "kosten": [],
            "voertalen": [{"voertaal_omschrijving": "Engels"}],
            "voorkeuren": [],
            "inschrijfperiodes": [],
            "enrollment_type": "regular",
            "infolinks": [],
            "id_cursus_blok": course.course_offering_id,
            "id_cursus": course.course_id,
            "studentnummer": "",
            "cursus": course.course_code,
            "collegejaar": int(course.academic_year) if course.academic_year else None,
            "blok": course.block or "",
            "periode_omschrijving": course.period_description or "",
            "periode_start_einddatum": course.period_date_range or "",
            "cursus_korte_naam": course.course_name,
            "opmerking_cursus": course.course_note or "",
            "opmerking_cursus_blok": course.course_block_note or "",
            "onderwijsvorm_omschrijving": course.teaching_form_description or "",
            "punten": self._parse_float(course.ec) or 0,
            "punteneenheid": course.ec_unit or "",
            "coordinerend_onderdeel_oms": course.coordinating_unit or "",
            "faculteit_naam": course.faculty or "",
            "categorie_omschrijving": course.category or "",
            "cursustype_omschrijving": course.course_type or "Cursus",
            "timeslots": "",
            "min_voorkeursgroepen": 0,
            "max_voorkeursgroepen": 0,
            "wachtlijst": "N",
            "locatie": "",
            "onderdeel_van": course.programme_part or "",
            "toelatingsproces": "N",
            "is_in_enrollment_period": False,
            "vol_geen_wachtlijst": False,
        }

    @staticmethod
    def _parse_bool_jn(value: object) -> bool | None:
        if value == "J":
            return True
        if value == "N":
            return False
        return None

    @staticmethod
    def _parse_float(value: object) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            return None

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

    @staticmethod
    def _format_time_decimal(value: object) -> str | None:
        if value is None or value == "":
            return None

        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        hours = int(number)
        minutes = int(round((number - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"
