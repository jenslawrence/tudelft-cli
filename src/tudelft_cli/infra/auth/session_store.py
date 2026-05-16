from __future__ import annotations

import json
from contextlib import suppress
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Protocol

import keyring
from keyring.errors import KeyringError, PasswordDeleteError
from pydantic import ValidationError as PydanticValidationError

from tudelft_cli.domain.errors import AuthenticationError
from tudelft_cli.domain.models import AuthSession
from tudelft_cli.infra.config.settings import APP_NAME, session_file


KEYRING_ACCOUNT = "session-token"


class KeyringBackend(Protocol):
    def get_password(self, service_name: str, username: str) -> str | None:
        raise NotImplementedError

    def set_password(self, service_name: str, username: str, password: str) -> None:
        raise NotImplementedError

    def delete_password(self, service_name: str, username: str) -> None:
        raise NotImplementedError


class SessionStore:
    def __init__(
        self,
        path: Path | None = None,
        keyring_backend: KeyringBackend = keyring,
    ) -> None:
        self.path = path or session_file()
        self.keyring = keyring_backend

    def save(self, session: AuthSession) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not session.access_token:
            raise AuthenticationError("No access token found. Run 'tudelft login' again.")

        try:
            self.keyring.set_password(
                APP_NAME,
                KEYRING_ACCOUNT,
                json.dumps({"access_token": session.access_token}),
            )
        except KeyringError as exc:
            raise AuthenticationError(
                "Could not store the session token in the OS keyring. "
                "Run 'tudelft login' again."
            ) from exc

        self._write_metadata(session)

    def load(self) -> AuthSession | None:
        if not self.path.exists():
            return None

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError):
            self.clear()
            return None

        if not isinstance(data, dict):
            self.clear()
            return None

        old_plaintext_token = data.get("access_token")
        if old_plaintext_token:
            return self._migrate_plaintext_session(data)

        try:
            metadata = AuthSession.model_validate(data)
        except PydanticValidationError:
            self.clear()
            return None

        if _is_expired(metadata):
            self.clear()
            return None

        access_token = self._load_access_token()
        if access_token is None:
            self.clear()
            return None

        return metadata.model_copy(update={"access_token": access_token})

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
        with suppress(KeyringError, PasswordDeleteError):
            self.keyring.delete_password(APP_NAME, KEYRING_ACCOUNT)

    def _migrate_plaintext_session(self, data: dict[str, object]) -> AuthSession | None:
        try:
            session = AuthSession.model_validate(data)
        except PydanticValidationError:
            self.clear()
            return None

        if _is_expired(session):
            self.clear()
            return None

        if not session.access_token:
            self.clear()
            return None

        try:
            self.keyring.set_password(
                APP_NAME,
                KEYRING_ACCOUNT,
                json.dumps({"access_token": session.access_token}),
            )
        except KeyringError as exc:
            self.clear()
            raise AuthenticationError(
                "Could not migrate the saved session token to the OS keyring. "
                "Run 'tudelft login' again."
            ) from exc

        self._write_metadata(session)
        return session

    def _load_access_token(self) -> str | None:
        try:
            secret = self.keyring.get_password(APP_NAME, KEYRING_ACCOUNT)
        except KeyringError as exc:
            raise AuthenticationError(
                "Could not read the saved session token from the OS keyring. "
                "Run 'tudelft login' again."
            ) from exc

        if not secret:
            return None

        try:
            data = json.loads(secret)
        except JSONDecodeError:
            return None

        access_token = data.get("access_token") if isinstance(data, dict) else None
        return access_token if isinstance(access_token, str) and access_token else None

    def _write_metadata(self, session: AuthSession) -> None:
        metadata = session.model_dump(
            mode="json",
            exclude={"access_token"},
            exclude_none=True,
        )
        self.path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _is_expired(session: AuthSession) -> bool:
    if session.expires_at is None:
        return False

    expires_at = session.expires_at
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        now = now.replace(tzinfo=None)

    return expires_at <= now
