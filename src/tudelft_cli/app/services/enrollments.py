from tudelft_cli.domain.errors import AuthenticationError
from tudelft_cli.domain.interfaces import AuthProvider, StudentPortal


class GetEnrollmentsService:
    def __init__(self, auth_provider: AuthProvider, portal: StudentPortal) -> None:
        self.auth_provider = auth_provider
        self.portal = portal

    def execute(self) -> dict:
        session = self.auth_provider.load_session()
        if session is None:
            raise AuthenticationError("Not logged in. Run 'tudelft login' first.")

        return {
            "courses": self.portal.get_course_enrollments(session),
            "exams": self.portal.get_exam_enrollments(session),
        }
