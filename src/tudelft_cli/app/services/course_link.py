from tudelft_cli.domain.errors import ValidationError
from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import CourseLink


class GetCourseLinkService:
    def __init__(self, portal: StudentPortal) -> None:
        self.portal = portal

    def execute(self, course_code: str) -> CourseLink:
        normalized = course_code.strip().upper()
        if not normalized:
            raise ValidationError("Provide a course code.")
        return self.portal.get_course_link(normalized)