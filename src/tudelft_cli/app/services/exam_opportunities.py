from tudelft_cli.domain.errors import AuthenticationError, ValidationError
from tudelft_cli.domain.interfaces import AuthProvider, StudentPortal
from tudelft_cli.domain.models import ExamOpportunity, SuggestedExamCourse


class GetExamOpportunitiesService:
    def __init__(self, auth_provider: AuthProvider, portal: StudentPortal) -> None:
        self.auth_provider = auth_provider
        self.portal = portal

    def execute(self, course_code: str) -> tuple[SuggestedExamCourse, list[ExamOpportunity]]:
        if not course_code.strip():
            raise ValidationError("Provide a course code.")

        session = self.auth_provider.load_session()
        if session is None:
            raise AuthenticationError("Not logged in. Run 'tudelft login' first.")

        return self.portal.get_exam_opportunities(session, course_code.strip().upper())
