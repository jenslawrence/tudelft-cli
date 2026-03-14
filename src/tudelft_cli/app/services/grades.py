from tudelft_cli.domain.errors import AuthenticationError
from tudelft_cli.domain.interfaces import AuthProvider, StudentPortal
from tudelft_cli.domain.models import Grade


class GetGradesService:
    def __init__(self, auth_provider: AuthProvider, portal: StudentPortal) -> None:
        self.auth_provider = auth_provider
        self.portal = portal

    def execute(self) -> list[Grade]:
        session = self.auth_provider.load_session()
        if session is None:
            raise AuthenticationError("Not logged in. Run 'tudelft login' first.")
        return list(self.portal.get_grades(session))
