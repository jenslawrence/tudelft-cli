from datetime import datetime, timedelta

from tudelft_cli.domain.interfaces import AuthProvider
from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.auth.session_store import SessionStore


class BrowserAuthProvider(AuthProvider):
    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store

    def login(self) -> AuthSession:
        # Placeholder for the real Playwright/browser-assisted SSO flow.
        # For now, we simulate a session so the rest of the app can be built.
        session = AuthSession(
            access_token="dev-token",
            expires_at=datetime.now() + timedelta(hours=1),
            netid="student",
        )
        self.session_store.save(session)
        return session

    def load_session(self) -> AuthSession | None:
        return self.session_store.load()

    def logout(self) -> None:
        self.session_store.clear()
