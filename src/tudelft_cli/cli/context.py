from __future__ import annotations

from dataclasses import dataclass

from tudelft_cli.domain.interfaces import AuthProvider, StudentPortal
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal


@dataclass(frozen=True)
class CliContext:
    auth: AuthProvider
    portal: StudentPortal


def create_context() -> CliContext:
    session_store = SessionStore()
    auth_provider = BrowserAuthProvider(session_store)
    portal = MyTUDelftPortal()
    return CliContext(auth=auth_provider, portal=portal)
