from __future__ import annotations

from typing import Any, Sequence

from tudelft_cli.domain.errors import PortalChangedError, ValidationError
from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import (
    AuthSession,
    CourseEnrollment,
    CourseLink,
    EcProgress,
    ExamEnrollment,
    ExamOpportunity,
    Grade,
    StudentProfile,
    SuggestedCourse,
    SuggestedExamCourse,
)
from tudelft_cli.infra.portal.client import PortalClient, httpx as httpx
from tudelft_cli.infra.portal.enrollment import (
    EnrollmentResponseState,
    validate_enrollment_response,
)
from tudelft_cli.infra.portal.mappers.courses import (
    build_course_enrollment_payload,
    map_course_enrollments_payload,
    map_suggested_courses_payload,
)
from tudelft_cli.infra.portal.mappers.exams import (
    build_exam_enrollment_payload,
    map_exam_enrollments_payload,
    map_exam_opportunities_payload,
    map_suggested_exam_courses_payload,
)
from tudelft_cli.infra.portal.mappers.grades import map_grades_page
from tudelft_cli.infra.portal.mappers.profile import map_profile_payload
from tudelft_cli.infra.portal.mappers.progress import map_ec_progress_payload
from tudelft_cli.infra.portal.parsing import (
    as_optional_string,
    format_time_decimal,
    parse_bool_jn,
    parse_datetime,
    parse_float,
    parse_int,
    required_string,
)


class MyTUDelftPortal(StudentPortal):
    BASE_URL = "https://my.tudelft.nl/student/osiris"
    RESULTS_PAGE_SIZE = 100
    COURSE_SUGGESTIONS_URL = (
        f"{BASE_URL}/student/cursussen_voor_cursusinschrijving/"
        "te_volgen_onderwijs/open_voor_inschrijving/"
    )
    COURSE_ENROLLMENTS_URL = f"{BASE_URL}/student/inschrijvingen/cursussen"
    EXAM_SUGGESTIONS_URL = (
        f"{BASE_URL}/student/cursussen_voor_toetsinschrijving/"
        "te_volgen_onderwijs/open_voor_inschrijving/"
    )
    EXAM_OPPORTUNITIES_URL = f"{BASE_URL}/student/cursussen_voor_toetsinschrijving"
    EXAM_ENROLLMENTS_URL = f"{BASE_URL}/student/inschrijvingen/toetsen/"
    STUDY_GUIDE_DEEPLINK_URL = "https://studiegids.tudelft.nl/courses/deeplink"

    _format_time_decimal = staticmethod(format_time_decimal)
    _parse_bool_jn = staticmethod(parse_bool_jn)
    _parse_float = staticmethod(parse_float)
    _required_string = staticmethod(required_string)
    _as_optional_string = staticmethod(as_optional_string)
    _parse_datetime = staticmethod(parse_datetime)
    _parse_int = staticmethod(parse_int)

    def __init__(self, client: PortalClient | None = None) -> None:
        self._client = client or PortalClient()

    def _build_headers(self, session: AuthSession) -> dict[str, str]:
        return self._client.build_headers(session)

    def get_course_link(self, course_code: str) -> CourseLink:
        normalized = course_code.strip().upper()
        if not normalized:
            raise ValidationError("Provide a course code.")

        url = f"{self.STUDY_GUIDE_DEEPLINK_URL}?code={normalized}"
        return CourseLink(course_code=normalized, study_guide_url=url)

    def get_profile(self, session: AuthSession) -> StudentProfile:
        payload = self._client.get_json(
            session,
            f"{self.BASE_URL}/gebruiker",
            unexpected_response_message="Unexpected response from gebruiker endpoint",
            invalid_json_message="Gebruiker endpoint did not return valid JSON.",
        )
        return map_profile_payload(payload)

    def get_grades(self, session: AuthSession, final_only: bool = False) -> Sequence[Grade]:
        url = f"{self.BASE_URL}/student/resultaten"
        offset = 0
        grades: list[Grade] = []

        while True:
            payload = self._client.get_json(
                session,
                url,
                params={"limit": self.RESULTS_PAGE_SIZE, "offset": offset},
                unexpected_response_message="Unexpected response from resultaten endpoint",
                invalid_json_message="Resultaten endpoint did not return valid JSON.",
            )
            page_grades, has_more = map_grades_page(payload, final_only=final_only)
            grades.extend(page_grades)

            if not has_more:
                break

            offset += self.RESULTS_PAGE_SIZE

        return grades

    def get_ec_progress(self, session: AuthSession) -> EcProgress:
        payload = self._client.get_json(
            session,
            f"{self.BASE_URL}/student/voortgang/per_opleiding/",
            unexpected_response_message="Unexpected response from voortgang endpoint",
            invalid_json_message="Voortgang endpoint did not return valid JSON.",
        )
        return map_ec_progress_payload(payload)

    def get_suggested_courses(self, session: AuthSession) -> list[SuggestedCourse]:
        payload = self._client.get_json(
            session,
            self.COURSE_SUGGESTIONS_URL,
            params={"limit": 9999},
            unexpected_response_message="Unexpected response from suggested courses endpoint",
            invalid_json_message="Suggested courses endpoint did not return valid JSON.",
        )
        return map_suggested_courses_payload(payload)

    def get_course_enrollments(self, session: AuthSession) -> list[CourseEnrollment]:
        payload = self._client.get_json(
            session,
            self.COURSE_ENROLLMENTS_URL,
            unexpected_response_message="Unexpected response from course enrollments endpoint",
            invalid_json_message="Course enrollments endpoint did not return valid JSON.",
        )
        return map_course_enrollments_payload(payload)

    def get_exam_enrollments(self, session: AuthSession) -> list[ExamEnrollment]:
        payload = self._client.get_json(
            session,
            self.EXAM_ENROLLMENTS_URL,
            unexpected_response_message="Unexpected response from exam enrollments endpoint",
            invalid_json_message="Exam enrollments endpoint did not return valid JSON.",
        )
        return map_exam_enrollments_payload(payload)

    def get_suggested_exam_courses(self, session: AuthSession) -> list[SuggestedExamCourse]:
        payload = self._client.get_json(
            session,
            self.EXAM_SUGGESTIONS_URL,
            params={"limit": 9999},
            unexpected_response_message="Unexpected response from suggested exams endpoint",
            invalid_json_message="Suggested exams endpoint did not return valid JSON.",
        )
        return map_suggested_exam_courses_payload(payload)

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
        payload = self._client.get_json(
            session,
            f"{self.EXAM_OPPORTUNITIES_URL}/{course_id}",
            unexpected_response_message="Unexpected response from exam opportunities endpoint",
            invalid_json_message="Exam opportunities endpoint did not return valid JSON.",
        )
        return map_exam_opportunities_payload(payload)

    def enroll_courses(self, session: AuthSession, course_codes: list[str]) -> list[CourseEnrollment]:
        existing_enrollments = self.get_course_enrollments(session)
        existing_codes = {item.course_code.upper() for item in existing_enrollments}
        codes_to_enroll = [code for code in course_codes if code not in existing_codes]

        if not codes_to_enroll:
            return [
                item for item in existing_enrollments if item.course_code.upper() in set(course_codes)
            ]

        suggestions = self.get_suggested_courses(session)
        by_code = {course.course_code.upper(): course for course in suggestions}

        missing = [code for code in codes_to_enroll if code not in by_code]
        if missing:
            raise ValidationError(f"Course(s) not found in suggested courses: {', '.join(missing)}")

        already_reported_by_portal: set[str] = set()

        for code in codes_to_enroll:
            course = by_code[code]
            url = f"{self.COURSE_ENROLLMENTS_URL}/{course.course_offering_id}"
            payload = self._client.put_json(
                session,
                url,
                json_body=build_course_enrollment_payload(course),
                unexpected_response_message=f"Unexpected response while enrolling in {code}",
                invalid_json_message=f"Enrollment response for {code} did not return valid JSON.",
            )

            state = validate_enrollment_response(payload, f"course enrollment for {code}")
            if state is EnrollmentResponseState.ALREADY_ENROLLED:
                already_reported_by_portal.add(code)

        enrollments = self.get_course_enrollments(session)
        enrolled_codes = {item.course_code.upper() for item in enrollments}
        not_verified = [code for code in codes_to_enroll if code not in enrolled_codes]
        if not_verified:
            already_not_verified = [
                code for code in not_verified if code in already_reported_by_portal
            ]
            if already_not_verified:
                raise PortalChangedError(
                    "Portal reported course enrollment already existed, but current "
                    f"enrollments do not include: {', '.join(already_not_verified)}"
                )
            raise PortalChangedError(
                "Enrollment could not be verified for: "
                f"{', '.join(not_verified)}. The portal response did not contain a "
                "failure message, but the course was not present afterwards."
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

        selected_offering_id = opportunities[selected_index].exam_offering_id
        existing_exam_enrollments = self.get_exam_enrollments(session)
        existing_matching = [
            item for item in existing_exam_enrollments if item.exam_offering_id == selected_offering_id
        ]
        if existing_matching:
            return existing_matching

        response_payload = self._client.post_json(
            session,
            self.EXAM_ENROLLMENTS_URL,
            json_body=build_exam_enrollment_payload(raw_items[selected_index]),
            unexpected_response_message=f"Unexpected response while enrolling exam for {course_code}",
            invalid_json_message=(
                f"Exam enrollment response for {course_code} did not return valid JSON."
            ),
        )
        state = validate_enrollment_response(
            response_payload, f"exam enrollment for {course_code}"
        )

        enrollments = self.get_exam_enrollments(session)
        matching = [item for item in enrollments if item.exam_offering_id == selected_offering_id]

        if not matching:
            if state is EnrollmentResponseState.ALREADY_ENROLLED:
                raise PortalChangedError(
                    f"Portal reported exam enrollment for {course_code} already existed, "
                    f"but current enrollments do not include exam offering {selected_offering_id}."
                )
            raise PortalChangedError(
                f"Exam enrollment could not be verified for {course_code}. The portal response "
                f"did not contain a failure message, but exam offering {selected_offering_id} "
                "was not present afterwards."
            )

        return matching
