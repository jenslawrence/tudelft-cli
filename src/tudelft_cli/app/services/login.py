from tudelft_cli.domain.interfaces import AuthProvider
from tudelft_cli.domain.models import AuthSession


class LoginService:
    def __init__(self, auth_provider: AuthProvider) -> None:
        self.auth_provider = auth_provider

    def execute(self) -> AuthSession:
        return self.auth_provider.login()
