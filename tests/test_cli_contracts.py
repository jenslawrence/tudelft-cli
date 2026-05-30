from __future__ import annotations

import importlib
import json
from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from tudelft_cli.cli.context import CliContext
from tudelft_cli.domain.models import (
    AuthSession,
    CourseEnrollment,
    CourseLink,
    EcPhaseProgress,
    EcProgress,
    ExamEnrollment,
    ExamOpportunity,
    Grade,
    StudentProfile,
    SuggestedCourse,
    SuggestedExamCourse,
)
from tudelft_cli.main import app


PUBLIC_COMMANDS = [
    "login",
    "logout",
    "status",
    "whoami",
    "grades",
    "ec",
    "enrollments",
    "suggest-courses",
    "suggest-exams",
    "enroll-course",
    "enroll-exam",
    "course",
]

CONTEXT_MODULES = [
    "tudelft_cli.cli.auth",
    "tudelft_cli.cli.whoami",
    "tudelft_cli.cli.grades",
    "tudelft_cli.cli.ec",
    "tudelft_cli.cli.enrollments",
    "tudelft_cli.cli.suggest_courses",
    "tudelft_cli.cli.suggest_exams",
    "tudelft_cli.cli.enroll_courses",
    "tudelft_cli.cli.enroll_exam",
    "tudelft_cli.cli.course",
]


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class FakeAuth:
    def __init__(self, session: AuthSession | None = None) -> None:
        self.session = session
        self.logout_called = False

    def login(self) -> AuthSession:
        return self.session or AuthSession(access_token="fake-token", token_type="Bearer")

    def load_session(self) -> AuthSession | None:
        return self.session

    def logout(self) -> None:
        self.logout_called = True


class FakePortal:
    def __init__(self) -> None:
        self.final_only: bool | None = None

    def get_profile(self, session: AuthSession) -> StudentProfile:
        return StudentProfile(
            name="Ada Lovelace",
            student_number="1234567",
            email="ada.lovelace@example.test",
        )

    def get_grades(self, session: AuthSession, final_only: bool = False) -> list[Grade]:
        self.final_only = final_only
        return [
            Grade(
                course_code="CSE2530",
                course_name="Software Engineering Methods",
                component="Final",
                value="8.5",
                passed=True,
                published_at=datetime(2026, 1, 12, 10, 15, tzinfo=timezone.utc),
            )
        ]

    def get_ec_progress(self, session: AuthSession) -> EcProgress:
        return EcProgress(
            items=[
                EcPhaseProgress(
                    programme_name="CSE",
                    faculty="EEMCS",
                    exam_programme_name="BSc CSE",
                    phase_description="Year 1",
                    earned_ec=42,
                    required_ec=60,
                    percentage=70,
                    completed=False,
                    other_earned_ec=3,
                )
            ]
        )

    def get_suggested_courses(self, session: AuthSession) -> list[SuggestedCourse]:
        return [
            SuggestedCourse(
                course_offering_id=1001,
                course_id=501,
                course_code="CSE2000",
                academic_year="2025",
                block="Q3",
                period_description="Semester 2",
                course_name="Software Project",
                faculty="EEMCS",
                ec="10",
                ec_unit="EC",
                availability=True,
            )
        ]

    def get_course_enrollments(self, session: AuthSession) -> list[CourseEnrollment]:
        return [
            CourseEnrollment(
                course_offering_id=1001,
                course_id=501,
                course_code="CSE2000",
                academic_year=2025,
                block="Q3",
                period_description="Semester 2",
                course_name="Software Project",
                ec=10.0,
                ec_unit="EC",
                programme_part="Core",
                can_unenroll=True,
            )
        ]

    def get_exam_enrollments(self, session: AuthSession) -> list[ExamEnrollment]:
        return [
            ExamEnrollment(
                exam_offering_id=9001,
                course_id=501,
                course_code="CSE2000",
                course_name="Software Project",
                test_description="Written exam",
                opportunity=1,
                exam_datetime=datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc),
                start_time="09:30",
                end_time="12:45",
                can_unenroll=False,
            )
        ]

    def enroll_courses(
        self,
        session: AuthSession,
        course_codes: list[str],
    ) -> list[CourseEnrollment]:
        raise AssertionError("enroll_courses should not be called by contract tests")

    def get_suggested_exam_courses(self, session: AuthSession) -> list[SuggestedExamCourse]:
        return [
            SuggestedExamCourse(
                course_id=501,
                course_code="CSE2000",
                academic_year=2025,
                course_name="Software Project",
                ec=10.0,
                ec_unit="EC",
                programme_part="Core",
            )
        ]

    def enroll_exam(
        self,
        session: AuthSession,
        course_code: str,
        selection: int | None = None,
    ) -> list[ExamEnrollment]:
        raise AssertionError("enroll_exam should not be called by contract tests")

    def get_exam_opportunities(
        self,
        session: AuthSession,
        course_code: str,
    ) -> tuple[SuggestedExamCourse, list[ExamOpportunity]]:
        raise AssertionError("get_exam_opportunities should not be called by contract tests")

    def get_course_link(self, course_code: str) -> CourseLink:
        normalized = course_code.strip().upper()
        return CourseLink(
            course_code=normalized,
            study_guide_url=f"https://studiegids.tudelft.nl/courses/deeplink?code={normalized}",
        )


def install_fake_context(
    monkeypatch: pytest.MonkeyPatch,
    *,
    auth: FakeAuth | None = None,
    portal: FakePortal | None = None,
) -> CliContext:
    context = CliContext(
        auth=auth or FakeAuth(AuthSession(access_token="fake-token")),
        portal=portal or FakePortal(),
    )

    for module_name in CONTEXT_MODULES:
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module, "create_context", lambda context=context: context)

    return context


@pytest.mark.parametrize("command", PUBLIC_COMMANDS)
def test_public_command_help_is_available(runner: CliRunner, command: str) -> None:
    result = runner.invoke(app, [command, "--help"], color=False)

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert command in result.output
    assert "Traceback" not in result.output


def test_root_help_lists_public_commands(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"], color=False)

    assert result.exit_code == 0
    assert "TU Delft student portal CLI." in result.output
    for command in PUBLIC_COMMANDS:
        assert command in result.output


def test_course_outputs_study_guide_link(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["course", "CSE2530"], color=False)

    assert result.exit_code == 0
    assert "CSE2530" in result.output
    assert "https://studiegids.tudelft.nl/courses/deeplink?code=CSE2530" in result.output


def test_course_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["course", "CSE2530", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"course_code", "study_guide_url"}
    assert payload["course_code"] == "CSE2530"
    assert payload["study_guide_url"].endswith("?code=CSE2530")


def test_course_requires_course_code(runner: CliRunner) -> None:
    result = runner.invoke(app, ["course"], color=False)

    assert result.exit_code != 0
    assert "Missing argument" in result.output
    assert "COURSE_CODE" in result.output
    assert "Traceback" not in result.output


def test_course_rejects_blank_course_code(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["course", ""], color=False)

    assert result.exit_code == 1
    assert "Error: Provide a course code." in result.output
    assert "Traceback" not in result.output


def test_course_rejects_invalid_output_format(runner: CliRunner) -> None:
    result = runner.invoke(app, ["course", "CSE2530", "--output", "yaml"], color=False)

    assert result.exit_code == 2
    assert "yaml" in result.output
    assert "--output" in result.output or "json" in result.output or "text" in result.output
    assert "Traceback" not in result.output


@pytest.mark.parametrize(
    ("args", "fragments"),
    [
        (["whoami"], ["Student Profile", "Ada Lovelace", "ada.lovelace@example.test"]),
        (["grades"], ["Grades", "CSE2530", "Software Engineering Methods", "8.5"]),
        (["ec"], ["EC Progress", "CSE", "Year 1", "42", "60"]),
        (["enrollments"], ["Courses", "Exams", "CSE2000", "Written"]),
        (["suggest-courses"], ["Suggested courses", "CSE2000", "Software Project"]),
    ],
)
def test_auth_required_commands_use_fake_context(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    args: list[str],
    fragments: list[str],
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, args, color=False)

    assert result.exit_code == 0
    for fragment in fragments:
        assert fragment in result.output
    assert "Traceback" not in result.output


def test_grades_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["grades", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"items"}
    assert len(payload["items"]) == 1
    assert payload["items"][0]["course_code"] == "CSE2530"
    assert payload["items"][0]["course_name"] == "Software Engineering Methods"
    assert payload["items"][0]["value"] == "8.5"
    assert payload["items"][0]["passed"] is True


def test_ec_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["ec", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"items"}
    assert len(payload["items"]) == 1
    assert payload["items"][0]["programme_name"] == "CSE"
    assert payload["items"][0]["phase_description"] == "Year 1"
    assert payload["items"][0]["earned_ec"] == 42
    assert payload["items"][0]["required_ec"] == 60


def test_whoami_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["whoami", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"profile"}
    assert payload["profile"] == {
        "name": "Ada Lovelace",
        "student_number": "1234567",
        "email": "ada.lovelace@example.test",
    }


def test_enrollments_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    result = runner.invoke(app, ["enrollments", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert set(payload) == {"course_enrollments", "exam_enrollments"}
    assert len(payload["course_enrollments"]) == 1
    assert len(payload["exam_enrollments"]) == 1
    assert payload["course_enrollments"][0]["course_code"] == "CSE2000"
    assert payload["course_enrollments"][0]["course_name"] == "Software Project"
    assert payload["course_enrollments"][0]["can_unenroll"] is True
    assert payload["exam_enrollments"][0]["course_code"] == "CSE2000"
    assert payload["exam_enrollments"][0]["test_description"] == "Written exam"
    assert payload["exam_enrollments"][0]["exam_datetime"] == "2026-04-20T09:00:00+00:00"


def test_enrollments_json_respects_course_and_exam_filters(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch)

    courses_result = runner.invoke(
        app,
        ["enrollments", "--courses", "--output", "json"],
        color=False,
    )
    exams_result = runner.invoke(
        app,
        ["enrollments", "--exams", "--output", "json"],
        color=False,
    )

    assert courses_result.exit_code == 0
    courses_payload = json.loads(courses_result.output)
    assert len(courses_payload["course_enrollments"]) == 1
    assert courses_payload["exam_enrollments"] == []

    assert exams_result.exit_code == 0
    exams_payload = json.loads(exams_result.output)
    assert exams_payload["course_enrollments"] == []
    assert len(exams_payload["exam_enrollments"]) == 1


def test_status_default_output_uses_local_session_without_secret(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    install_fake_context(
        monkeypatch,
        auth=FakeAuth(AuthSession(access_token="secret-token", expires_at=expires_at)),
    )

    result = runner.invoke(app, ["status"], color=False)

    assert result.exit_code == 0
    assert "Auth Status" in result.output
    assert "Authenticated" in result.output
    assert expires_at.isoformat() in result.output
    assert "secret-token" not in result.output
    assert "Traceback" not in result.output


def test_status_json_output_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    install_fake_context(
        monkeypatch,
        auth=FakeAuth(AuthSession(access_token="secret-token", expires_at=expires_at)),
    )

    result = runner.invoke(app, ["status", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {
        "authenticated": True,
        "expires_at": expires_at.isoformat(),
        "expired": False,
    }
    assert "secret-token" not in result.output


def test_status_json_expired_session_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    install_fake_context(
        monkeypatch,
        auth=FakeAuth(AuthSession(access_token="secret-token", expires_at=expires_at)),
    )

    result = runner.invoke(app, ["status", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {
        "authenticated": False,
        "expires_at": expires_at.isoformat(),
        "expired": True,
    }
    assert "secret-token" not in result.output


def test_status_default_output_handles_missing_session(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch, auth=FakeAuth(session=None))

    result = runner.invoke(app, ["status"], color=False)

    assert result.exit_code == 0
    assert "Auth Status" in result.output
    assert "Authenticated" in result.output
    assert "no" in result.output
    assert "Traceback" not in result.output


def test_status_json_missing_session_contract(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch, auth=FakeAuth(session=None))

    result = runner.invoke(app, ["status", "--output", "json"], color=False)

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {
        "authenticated": False,
        "expires_at": None,
        "expired": None,
    }


def test_grades_final_only_option_reaches_portal(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    portal = FakePortal()
    install_fake_context(monkeypatch, portal=portal)

    result = runner.invoke(app, ["grades", "--final-only"], color=False)

    assert result.exit_code == 0
    assert portal.final_only is True


def test_missing_session_reports_user_facing_error_without_traceback(
    runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_context(monkeypatch, auth=FakeAuth(session=None))

    result = runner.invoke(app, ["whoami"], color=False)

    assert result.exit_code == 1
    assert "Error: Not logged in. Run 'tudelft login' first." in result.output
    assert "Traceback" not in result.output
