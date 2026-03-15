from tudelft_cli.domain.errors import AuthenticationError, ValidationError
from tudelft_cli.domain.interfaces import AuthProvider, StudentPortal
from tudelft_cli.domain.models import CourseEnrollment


class EnrollCoursesService:
    def __init__(self, auth_provider: AuthProvider, portal: StudentPortal) -> None:
        self.auth_provider = auth_provider
        self.portal = portal

    def execute(self, course_codes: list[str]) -> list[CourseEnrollment]:
        if not course_codes:
            raise ValidationError("Provide at least one course code.")

        session = self.auth_provider.load_session()
        if session is None:
            raise AuthenticationError("Not logged in. Run 'tudelft login' first.")

        normalized = [code.strip().upper() for code in course_codes if code.strip()]
        if not normalized:
            raise ValidationError("Provide at least one valid course code.")

        return self.portal.enroll_courses(session, normalized)
