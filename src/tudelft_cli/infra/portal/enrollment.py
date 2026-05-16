from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from tudelft_cli.domain.errors import PortalChangedError, ValidationError


class EnrollmentResponseState(Enum):
    ACCEPTED = "accepted"
    ALREADY_ENROLLED = "already_enrolled"


@dataclass(frozen=True)
class PortalStatusMessage:
    severity: str | None
    text: str


_FAILURE_STATUS_TYPES = {
    "ERROR",
    "FOUT",
    "FAIL",
    "FAILED",
    "FAILURE",
    "DANGER",
}
_ALREADY_ENROLLED_TEXT_MARKERS = (
    "already enrolled",
    "already registered",
    "already signed up",
    "al ingeschreven",
    "reeds ingeschreven",
)
_FAILURE_TEXT_MARKERS = (
    "error",
    "failed",
    "failure",
    "not possible",
    "not allowed",
    "not permitted",
    "cannot",
    "can't",
    "closed",
    "deadline",
    "full",
    "fout",
    "mislukt",
    "niet gelukt",
    "niet mogelijk",
    "niet toegestaan",
    "kan niet",
    "gesloten",
    "vol",
    "geen plaats",
)


def validate_enrollment_response(
    payload: object, action_description: str
) -> EnrollmentResponseState:
    messages = _extract_status_messages(payload, action_description)

    if any(_is_already_enrolled_message(message) for message in messages):
        return EnrollmentResponseState.ALREADY_ENROLLED

    failure_messages = [message for message in messages if _is_failure_message(message)]
    if failure_messages:
        raise ValidationError(
            f"Portal rejected {action_description}: {_format_status_messages(failure_messages)}"
        )

    return EnrollmentResponseState.ACCEPTED


def _extract_status_messages(
    payload: object, action_description: str
) -> list[PortalStatusMessage]:
    if not isinstance(payload, dict):
        raise PortalChangedError(
            f"Portal returned an unexpected response for {action_description}: "
            "expected a JSON object with statusmeldingen."
        )

    statusmeldingen = payload.get("statusmeldingen")
    if not isinstance(statusmeldingen, list):
        raise PortalChangedError(
            f"Portal returned an unknown response for {action_description}: "
            "missing statusmeldingen."
        )

    messages: list[PortalStatusMessage] = []
    for index, item in enumerate(statusmeldingen):
        message = _parse_status_message(item)
        if message is None:
            raise PortalChangedError(
                f"Portal returned malformed statusmeldingen for {action_description}: "
                f"entry {index + 1} did not contain a recognizable message."
            )
        messages.append(message)

    return messages


def _parse_status_message(item: object) -> PortalStatusMessage | None:
    if isinstance(item, str):
        return PortalStatusMessage(severity=None, text=item.strip())

    if not isinstance(item, dict):
        return None

    severity = _first_string_value(
        item,
        ("type", "severity", "niveau", "status", "soort", "categorie"),
    )
    text = _first_string_value(
        item,
        ("tekst", "text", "message", "melding", "omschrijving", "description", "titel"),
    )

    if text is None:
        string_values = [
            value.strip() for value in item.values() if isinstance(value, str) and value.strip()
        ]
        if severity is not None:
            string_values = [value for value in string_values if value != severity]
        text = " ".join(string_values) or None

    if severity is None and text is None:
        return None

    return PortalStatusMessage(severity=severity, text=text or severity or "")


def _first_string_value(item: dict[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_already_enrolled_message(message: PortalStatusMessage) -> bool:
    text = message.text.casefold()
    return any(marker in text for marker in _ALREADY_ENROLLED_TEXT_MARKERS)


def _is_failure_message(message: PortalStatusMessage) -> bool:
    severity = (message.severity or "").strip().upper()
    if severity in _FAILURE_STATUS_TYPES:
        return True

    text = message.text.casefold()
    return any(marker in text for marker in _FAILURE_TEXT_MARKERS)


def _format_status_messages(messages: Sequence[PortalStatusMessage]) -> str:
    parts = []
    for message in messages:
        if message.severity:
            parts.append(f"{message.severity}: {message.text}")
        else:
            parts.append(message.text)
    return "; ".join(parts)
