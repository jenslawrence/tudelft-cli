from datetime import datetime
from typing import Sequence

from tudelft_cli.domain.interfaces import StudentPortal
from tudelft_cli.domain.models import AuthSession, Grade, StudentProfile


class MyTUDelftPortal(StudentPortal):
    def get_profile(self, session: AuthSession) -> StudentProfile:
        return StudentProfile(
            name="Demo Student",
            netid=session.netid,
            student_number=session.student_number,
            programme="Computer Science",
            faculty="EEMCS",
        )

    def get_grades(self, session: AuthSession) -> Sequence[Grade]:
        return [
            Grade(
                course_code="CSE1010",
                course_name="Algorithms and Data Structures",
                component="Final grade",
                value="8.5",
                passed=True,
                published_at=datetime.now(),
            ),
            Grade(
                course_code="WI1006",
                course_name="Linear Algebra",
                component="Retake",
                value="7.0",
                passed=True,
                published_at=datetime.now(),
            ),
        ]
