from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from tudelft_cli.domain.models import (
    AuthSession,
    CourseEnrollment,
    ExamEnrollment,
    EcProgress,
    Grade,
    StudentProfile,
    SuggestedCourse,
    ExamOpportunity,
    SuggestedExamCourse,
)

class AuthProvider(ABC):
    @abstractmethod
    def login(self) -> AuthSession:
        raise NotImplementedError

    @abstractmethod
    def load_session(self) -> AuthSession | None:
        raise NotImplementedError

    @abstractmethod
    def logout(self) -> None:
        raise NotImplementedError


class StudentPortal(ABC):
    @abstractmethod
    def get_profile(self, session: AuthSession) -> StudentProfile:
        raise NotImplementedError

    @abstractmethod
    def get_grades(self, session: AuthSession) -> Sequence[Grade]:
        raise NotImplementedError

    @abstractmethod
    def get_ec_progress(self, session: AuthSession) -> EcProgress:
        raise NotImplementedError

    @abstractmethod
    def get_suggested_courses(self, session: AuthSession) -> list[SuggestedCourse]:
        raise NotImplementedError

    @abstractmethod
    def get_course_enrollments(self, session: AuthSession) -> list[CourseEnrollment]:
        raise NotImplementedError

    @abstractmethod
    def get_exam_enrollments(self, session: AuthSession) -> list[ExamEnrollment]:
        raise NotImplementedError

    @abstractmethod
    def enroll_courses(self, session: AuthSession, course_codes: list[str]) -> list[CourseEnrollment]:
        raise NotImplementedError

    @abstractmethod
    def get_suggested_exam_courses(self, session: AuthSession) -> list[SuggestedExamCourse]:
        raise NotImplementedError

    @abstractmethod
    def enroll_exam(
        self,
        session: AuthSession,
        course_code: str,
        selection: int | None = None,
    ) -> list[ExamEnrollment]:
        raise NotImplementedError

    @abstractmethod
    def get_exam_opportunities(
        self,
        session: AuthSession,
        course_code: str,
    ) -> tuple[SuggestedExamCourse, list[ExamOpportunity]]:
        raise NotImplementedError
