from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from keyring.errors import KeyringError, PasswordDeleteError

from tudelft_cli.domain.errors import AuthenticationError
from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.auth.browser_auth import _extract_expires_at
from tudelft_cli.infra.auth.session_store import KEYRING_ACCOUNT, SessionStore
from tudelft_cli.infra.config.settings import APP_NAME


class FakeKeyring:
    def __init__(self) -> None:
        self.secrets: dict[tuple[str, str], str] = {}
        self.fail_get = False
        self.fail_set = False
        self.fail_delete = False

    def get_password(self, service_name: str, username: str) -> str | None:
        if self.fail_get:
            raise KeyringError("keyring unavailable")
        return self.secrets.get((service_name, username))

    def set_password(self, service_name: str, username: str, password: str) -> None:
        if self.fail_set:
            raise KeyringError("keyring unavailable")
        self.secrets[(service_name, username)] = password

    def delete_password(self, service_name: str, username: str) -> None:
        if self.fail_delete:
            raise PasswordDeleteError("delete failed")
        self.secrets.pop((service_name, username), None)


def test_save_stores_token_in_keyring_and_metadata_in_json(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    session = AuthSession(
        access_token="secret-token",
        token_type="Bearer",
        scope="openid",
        expires_at=datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc),
    )

    SessionStore(session_path, keyring).save(session)

    metadata = json.loads(session_path.read_text(encoding="utf-8"))
    secret = json.loads(keyring.secrets[(APP_NAME, KEYRING_ACCOUNT)])
    assert "access_token" not in metadata
    assert metadata["token_type"] == "Bearer"
    assert metadata["scope"] == "openid"
    assert secret == {"access_token": "secret-token"}


def test_load_rehydrates_access_token_from_keyring(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    store = SessionStore(session_path, keyring)
    store.save(AuthSession(access_token="secret-token", token_type="Bearer"))

    session = store.load()

    assert session is not None
    assert session.access_token == "secret-token"
    assert session.token_type == "Bearer"


def test_load_migrates_old_plaintext_session_file(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    session_path.write_text(
        AuthSession(access_token="old-token", token_type="Bearer").model_dump_json(),
        encoding="utf-8",
    )

    session = SessionStore(session_path, keyring).load()

    metadata = json.loads(session_path.read_text(encoding="utf-8"))
    secret = json.loads(keyring.secrets[(APP_NAME, KEYRING_ACCOUNT)])
    assert session is not None
    assert session.access_token == "old-token"
    assert "access_token" not in metadata
    assert secret == {"access_token": "old-token"}


def test_load_clears_expired_session(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    store = SessionStore(session_path, keyring)
    store.save(
        AuthSession(
            access_token="secret-token",
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )

    assert store.load() is None
    assert not session_path.exists()
    assert (APP_NAME, KEYRING_ACCOUNT) not in keyring.secrets


def test_load_clears_missing_keyring_entry(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    session_path.write_text(
        AuthSession(token_type="Bearer").model_dump_json(exclude_none=True),
        encoding="utf-8",
    )

    assert SessionStore(session_path, keyring).load() is None
    assert not session_path.exists()


def test_load_clears_corrupt_keyring_entry(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    session_path = tmp_path / "session.json"
    session_path.write_text(
        AuthSession(token_type="Bearer").model_dump_json(exclude_none=True),
        encoding="utf-8",
    )
    keyring.secrets[(APP_NAME, KEYRING_ACCOUNT)] = "not-json"

    assert SessionStore(session_path, keyring).load() is None
    assert not session_path.exists()
    assert (APP_NAME, KEYRING_ACCOUNT) not in keyring.secrets


def test_load_reports_keyring_read_failure(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    keyring.fail_get = True
    session_path = tmp_path / "session.json"
    session_path.write_text(
        AuthSession(token_type="Bearer").model_dump_json(exclude_none=True),
        encoding="utf-8",
    )

    with pytest.raises(AuthenticationError, match="Run 'tudelft login' again"):
        SessionStore(session_path, keyring).load()


def test_plaintext_migration_failure_clears_file(tmp_path: Path) -> None:
    keyring = FakeKeyring()
    keyring.fail_set = True
    session_path = tmp_path / "session.json"
    session_path.write_text(
        AuthSession(access_token="old-token", token_type="Bearer").model_dump_json(),
        encoding="utf-8",
    )

    with pytest.raises(AuthenticationError, match="Run 'tudelft login' again"):
        SessionStore(session_path, keyring).load()

    assert not session_path.exists()


def test_extract_expires_at_uses_expires_in() -> None:
    before = datetime.now(timezone.utc) + timedelta(minutes=59)
    expires_at = _extract_expires_at({"expires_in": 3600, "access_token": "token"})
    after = datetime.now(timezone.utc) + timedelta(minutes=61)

    assert expires_at is not None
    assert before <= expires_at <= after


def test_extract_expires_at_uses_iso_timestamp() -> None:
    expires_at = _extract_expires_at(
        {
            "expires_at": "2026-05-16T12:00:00Z",
            "access_token": "token",
        }
    )

    assert expires_at == datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc)


def test_extract_expires_at_uses_jwt_exp_claim() -> None:
    payload = _base64url_json({"exp": 1_779_000_000})
    token = f"header.{payload}.signature"

    assert _extract_expires_at({"access_token": token}) == datetime.fromtimestamp(
        1_779_000_000,
        tz=timezone.utc,
    )


def _base64url_json(data: dict[str, object]) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(data).encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")
