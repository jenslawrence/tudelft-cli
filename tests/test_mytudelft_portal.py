from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from tudelft_cli.domain.errors import PortalChangedError, ValidationError
from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.portal import mytudelft_portal
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mytudelft"


class FakeResponse:
    def __init__(self, status_code: int, payload: object | None = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return copy.deepcopy(self._payload)


class FakeHttp:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], list[FakeResponse]] = {}
        self.calls: list[dict[str, Any]] = []

    def add(self, method: str, url: str, response: FakeResponse) -> None:
        self.routes.setdefault((method, url), []).append(response)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._request("GET", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._request("PUT", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        responses = self.routes.get((method, url))
        if not responses:
            raise AssertionError(f"Unexpected {method} request to {url}")
        return responses.pop(0)


@pytest.fixture
def session() -> AuthSession:
    return AuthSession(access_token="token")


@pytest.fixture
def fake_http(monkeypatch: pytest.MonkeyPatch) -> FakeHttp:
    fake = FakeHttp()
    monkeypatch.setattr(mytudelft_portal.httpx, "get", fake.get)
    monkeypatch.setattr(mytudelft_portal.httpx, "put", fake.put)
    monkeypatch.setattr(mytudelft_portal.httpx, "post", fake.post)
    return fake


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_format_time_decimal_formats_numeric_values() -> None:
    assert MyTUDelftPortal._format_time_decimal("9.5") == "09:30"


def test_format_time_decimal_keeps_non_numeric_values() -> None:
    assert MyTUDelftPortal._format_time_decimal("morning") == "morning"


def test_grades_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.BASE_URL}/student/resultaten",
        FakeResponse(200, load_fixture("grades_payload.json")),
    )

    grades = list(MyTUDelftPortal().get_grades(session))

    assert len(grades) == 3
    assert grades[0].course_code == "CSE1010"
    assert grades[0].course_name == "Algorithms"
    assert grades[0].component == "Final"
    assert grades[0].value == "8.5"
    assert grades[0].passed is True
    assert grades[0].published_at == datetime(2026, 1, 12, 10, 15, tzinfo=timezone.utc)
    assert grades[1].passed is False
    assert grades[1].published_at is None
    assert grades[2].passed is None


def test_grades_final_only_keeps_current_component_filter(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.BASE_URL}/student/resultaten",
        FakeResponse(200, load_fixture("grades_payload.json")),
    )

    grades = list(MyTUDelftPortal().get_grades(session, final_only=True))

    assert [grade.component for grade in grades] == ["Final", "Final grade"]


def test_ec_progress_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.BASE_URL}/student/voortgang/per_opleiding/",
        FakeResponse(200, load_fixture("ec_progress_payload.json")),
    )

    progress = MyTUDelftPortal().get_ec_progress(session)

    assert len(progress.items) == 2
    first = progress.items[0]
    assert first.programme_name == "Computer Science"
    assert first.faculty == "EEMCS"
    assert first.exam_programme_name == "BSc CSE"
    assert first.phase_description == "Bachelor year 1"
    assert first.earned_ec == 42
    assert first.required_ec == 60
    assert first.percentage == 70
    assert first.completed is False
    assert first.other_earned_ec == 3
    assert progress.items[1].completed is True


def test_suggested_courses_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_courses_payload.json")),
    )

    suggestions = MyTUDelftPortal().get_suggested_courses(session)

    assert len(suggestions) == 1
    course = suggestions[0]
    assert course.course_offering_id == 1001
    assert course.course_id == 501
    assert course.course_code == "CSE2000"
    assert course.academic_year == "2025"
    assert course.block == "Q3"
    assert course.course_name == "Software Project"
    assert course.ec == "10"
    assert course.ec_unit == "EC"
    assert course.availability is True
    assert course.waiting_list is None
    assert course.teaching_form_description == "Project"
    assert course.period_date_range is None


def test_course_enrollments_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("course_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().get_course_enrollments(session)

    assert len(enrollments) == 1
    enrollment = enrollments[0]
    assert enrollment.course_offering_id == 1001
    assert enrollment.course_id == 501
    assert enrollment.course_code == "CSE2000"
    assert enrollment.academic_year == 2025
    assert enrollment.period_date_range == "2026-02-01 - 2026-04-15"
    assert enrollment.ec == 10.0
    assert enrollment.can_unenroll is True
    assert enrollment.is_new is False
    assert enrollment.is_historical is None


def test_exam_opportunities_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )

    course, opportunities = MyTUDelftPortal().get_exam_opportunities(session, "cse2000")

    assert course.course_id == 501
    assert course.course_code == "CSE2000"
    assert course.academic_year == 2025
    assert course.ec == 10.0
    assert len(opportunities) == 2
    first = opportunities[0]
    assert first.exam_offering_id == 9001
    assert first.test_code == "T1"
    assert first.test_description == "Written exam"
    assert first.test_type_description == "Written"
    assert first.opportunity == 1
    assert first.exam_datetime == datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc)
    assert first.start_time == "09:30"
    assert first.end_time == "12:45"
    assert opportunities[1].start_time == "morning"


def test_exam_enrollments_payload_mapping(fake_http: FakeHttp, session: AuthSession) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("exam_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().get_exam_enrollments(session)

    assert len(enrollments) == 1
    enrollment = enrollments[0]
    assert enrollment.exam_offering_id == 9001
    assert enrollment.course_id == 501
    assert enrollment.course_code == "CSE2000"
    assert enrollment.course_name == "Software Project"
    assert enrollment.test_code == "T1"
    assert enrollment.test_description == "Written exam"
    assert enrollment.opportunity == 1
    assert enrollment.exam_datetime == datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc)
    assert enrollment.start_time == "09:30"
    assert enrollment.end_time == "12:45"
    assert enrollment.can_unenroll is False
    assert enrollment.is_new is True
    assert enrollment.result is None
    assert enrollment.is_historical is False


def test_course_enrollment_success_verifies_current_enrollment(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_courses_payload.json")),
    )
    fake_http.add(
        "PUT",
        f"{MyTUDelftPortal.COURSE_ENROLLMENTS_URL}/1001",
        FakeResponse(200, {"statusmeldingen": [{"type": "INFO", "tekst": "Ingeschreven"}]}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("course_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().enroll_courses(session, ["CSE2000"])

    assert [enrollment.course_code for enrollment in enrollments] == ["CSE2000"]
    put_call = next(call for call in fake_http.calls if call["method"] == "PUT")
    assert put_call["json"]["id_cursus_blok"] == 1001
    assert put_call["json"]["enrollment_type"] == "regular"
    assert put_call["json"]["punten"] == 10.0


def test_course_enrollment_returns_existing_enrollment_without_mutation(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("course_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().enroll_courses(session, ["CSE2000"])

    assert [enrollment.course_code for enrollment in enrollments] == ["CSE2000"]
    assert not [call for call in fake_http.calls if call["method"] == "PUT"]


def test_course_enrollment_rejects_explicit_portal_failure_message(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_courses_payload.json")),
    )
    fake_http.add(
        "PUT",
        f"{MyTUDelftPortal.COURSE_ENROLLMENTS_URL}/1001",
        FakeResponse(200, {"statusmeldingen": [{"type": "ERROR", "tekst": "Already full"}]}),
    )

    with pytest.raises(ValidationError, match="Portal rejected course enrollment for CSE2000"):
        MyTUDelftPortal().enroll_courses(session, ["CSE2000"])


def test_course_enrollment_rejects_missing_status_messages(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_courses_payload.json")),
    )
    fake_http.add(
        "PUT",
        f"{MyTUDelftPortal.COURSE_ENROLLMENTS_URL}/1001",
        FakeResponse(200, {"message": "ok"}),
    )

    with pytest.raises(PortalChangedError, match="missing statusmeldingen"):
        MyTUDelftPortal().enroll_courses(session, ["CSE2000"])


def test_course_enrollment_fails_when_verification_enrollment_is_absent(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_courses_payload.json")),
    )
    fake_http.add(
        "PUT",
        f"{MyTUDelftPortal.COURSE_ENROLLMENTS_URL}/1001",
        FakeResponse(200, {"statusmeldingen": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.COURSE_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )

    with pytest.raises(PortalChangedError, match="Enrollment could not be verified for: CSE2000"):
        MyTUDelftPortal().enroll_courses(session, ["CSE2000"])


def test_exam_enrollment_verifies_by_exam_offering_id(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "POST",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"statusmeldingen": [{"type": "INFO", "tekst": "Ingeschreven"}]}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("exam_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().enroll_exam(session, "CSE2000", selection=1)

    assert [enrollment.exam_offering_id for enrollment in enrollments] == [9001]
    post_call = next(call for call in fake_http.calls if call["method"] == "POST")
    assert post_call["json"]["toetsen"][0]["id_toets_gelegenheid"] == "9001"
    assert post_call["json"]["toetsen"][0]["tijd_vanaf"] == "09:30"
    assert post_call["json"]["toetsen"][0]["tijd_tm"] == "12:45"
    assert post_call["json"]["toetsen"][0]["voorzieningen"] == []
    assert post_call["json"]["toetsen"][0]["renderIndex"] == 0


def test_exam_enrollment_returns_existing_enrollment_without_mutation(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, load_fixture("exam_enrollments_payload.json")),
    )

    enrollments = MyTUDelftPortal().enroll_exam(session, "CSE2000", selection=1)

    assert [enrollment.exam_offering_id for enrollment in enrollments] == [9001]
    assert not [call for call in fake_http.calls if call["method"] == "POST"]


def test_exam_enrollment_rejects_explicit_portal_failure_message(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "POST",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"statusmeldingen": [{"type": "ERROR", "tekst": "Enrollment closed"}]}),
    )

    with pytest.raises(ValidationError, match="Portal rejected exam enrollment for CSE2000"):
        MyTUDelftPortal().enroll_exam(session, "CSE2000", selection=1)


def test_exam_enrollment_rejects_malformed_response(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "POST",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, ["not", "an", "object"]),
    )

    with pytest.raises(PortalChangedError, match="expected a JSON object"):
        MyTUDelftPortal().enroll_exam(session, "CSE2000", selection=1)


def test_exam_enrollment_fails_when_exam_offering_id_is_not_verified(
    fake_http: FakeHttp,
    session: AuthSession,
) -> None:
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_SUGGESTIONS_URL,
        FakeResponse(200, load_fixture("suggested_exam_courses_payload.json")),
    )
    fake_http.add(
        "GET",
        f"{MyTUDelftPortal.EXAM_OPPORTUNITIES_URL}/501",
        FakeResponse(200, load_fixture("exam_opportunities_payload.json")),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )
    fake_http.add(
        "POST",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"statusmeldingen": []}),
    )
    fake_http.add(
        "GET",
        MyTUDelftPortal.EXAM_ENROLLMENTS_URL,
        FakeResponse(200, {"items": []}),
    )

    with pytest.raises(PortalChangedError, match="Exam enrollment could not be verified for CSE2000"):
        MyTUDelftPortal().enroll_exam(session, "CSE2000", selection=1)
