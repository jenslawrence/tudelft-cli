from tudelft_cli.cli.context import CliContext, create_context
from tudelft_cli.infra.auth.browser_auth import BrowserAuthProvider
from tudelft_cli.infra.auth.session_store import SessionStore
from tudelft_cli.infra.portal.mytudelft_portal import MyTUDelftPortal


def test_create_context_wires_cli_dependencies() -> None:
    context = create_context()

    assert isinstance(context, CliContext)
    assert isinstance(context.auth, BrowserAuthProvider)
    assert isinstance(context.auth.session_store, SessionStore)
    assert isinstance(context.portal, MyTUDelftPortal)
