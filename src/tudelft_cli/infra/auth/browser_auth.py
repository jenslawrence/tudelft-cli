from __future__ import annotations

from datetime import datetime
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from tudelft_cli.domain.errors import AuthenticationError, LoginTimeoutError
from tudelft_cli.domain.interfaces import AuthProvider
from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.auth.session_store import SessionStore


class BrowserAuthProvider(AuthProvider):
    TOKEN_URL = "https://my.tudelft.nl/student/osiris/token"
    LOGIN_URL = "https://my.tudelft.nl"

    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store

    def login(self) -> AuthSession:
        token_payload: dict[str, Any] | None = None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            def handle_response(response: Any) -> None:
                nonlocal token_payload

                if response.request.method != "POST":
                    return
                if not response.url.startswith(self.TOKEN_URL):
                    return

                try:
                    payload = response.json()
                except Exception:
                    return

                if (
                    isinstance(payload, dict)
                    and isinstance(payload.get("access_token"), str)
                    and payload.get("access_token")
                ):
                    token_payload = payload

            page.on("response", handle_response)

            try:
                page.goto(self.LOGIN_URL, wait_until="domcontentloaded")
                page.wait_for_url("https://my.tudelft.nl/**", timeout=300_000)
                page.wait_for_timeout(2_000)

                deadline_ms = 300_000
                poll_interval_ms = 500
                waited_ms = 0

                while token_payload is None and waited_ms < deadline_ms:
                    page.wait_for_timeout(poll_interval_ms)
                    waited_ms += poll_interval_ms

                if token_payload is None:
                    raise LoginTimeoutError(
                        "Login succeeded in the browser, but no OSIRIS token was captured."
                    )

                session = AuthSession(
                    access_token=token_payload["access_token"],
                    token_type=token_payload.get("token_type"),
                    scope=token_payload.get("scope"),
                    obtained_at=datetime.now(),
                )
                self.session_store.save(session)
                return session

            except PlaywrightTimeoutError as exc:
                raise LoginTimeoutError(
                    "Timed out waiting for TU Delft login to complete."
                ) from exc
            except LoginTimeoutError:
                raise
            except Exception as exc:
                raise AuthenticationError(f"Browser login failed: {exc}") from exc
            finally:
                context.close()
                browser.close()

    def load_session(self) -> AuthSession | None:
        return self.session_store.load()

    def logout(self) -> None:
        self.session_store.clear()
