from __future__ import annotations

import base64
import contextlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from tudelft_cli.domain.errors import AuthenticationError, LoginTimeoutError, MissingBrowserError
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
            try:
                browser = playwright.chromium.launch(headless=False)
            except Exception as exc:
                message = str(exc)

                if "Executable doesn't exist" in message or "playwright install" in message.lower():
                    raise MissingBrowserError(
                        "Playwright browser not installed.\n\n"
                        "Run:\n"
                        "  playwright install chromium"
                    ) from exc

                raise

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
                    expires_at=_extract_expires_at(token_payload),
                    obtained_at=datetime.now(timezone.utc),
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


def _extract_expires_at(token_payload: dict[str, Any]) -> datetime | None:
    obtained_at = datetime.now(timezone.utc)

    expires_in = token_payload.get("expires_in")
    if isinstance(expires_in, str):
        with contextlib.suppress(ValueError):
            expires_in = int(expires_in)
    if isinstance(expires_in, int | float):
        return obtained_at + timedelta(seconds=expires_in)

    for field in ("expires_at", "expires_on", "expires"):
        expires_at = _parse_datetime_value(token_payload.get(field))
        if expires_at is not None:
            return expires_at

    access_token = token_payload.get("access_token")
    if isinstance(access_token, str):
        return _extract_jwt_expires_at(access_token)

    return None


def _parse_datetime_value(value: object) -> datetime | None:
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if not isinstance(value, str) or not value:
        return None

    with contextlib.suppress(ValueError):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)

    with contextlib.suppress(ValueError):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    return None


def _extract_jwt_expires_at(access_token: str) -> datetime | None:
    parts = access_token.split(".")
    if len(parts) < 2:
        return None

    payload = parts[1]
    padding = "=" * (-len(payload) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{payload}{padding}")
        data = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None

    return _parse_datetime_value(data.get("exp"))
