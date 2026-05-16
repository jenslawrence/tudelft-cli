from __future__ import annotations

from typing import Literal, Mapping

import httpx

from tudelft_cli.domain.errors import AuthenticationError, PortalChangedError
from tudelft_cli.domain.models import AuthSession


HttpMethod = Literal["GET", "POST", "PUT"]
QueryParams = Mapping[str, str | int | float | bool | None]


class PortalClient:
    def build_headers(self, session: AuthSession) -> dict[str, str]:
        if not session.access_token:
            raise AuthenticationError("No access token found. Run 'tudelft login' first.")

        return {
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {session.access_token}",
            "client_type": "web",
            "Content-Type": "application/json",
            "taal": "NL",
        }

    def get_json(
        self,
        session: AuthSession,
        url: str,
        *,
        unexpected_response_message: str,
        invalid_json_message: str,
        params: QueryParams | None = None,
    ) -> object:
        return self._request_json(
            "GET",
            session,
            url,
            unexpected_response_message=unexpected_response_message,
            invalid_json_message=invalid_json_message,
            params=params,
        )

    def put_json(
        self,
        session: AuthSession,
        url: str,
        *,
        unexpected_response_message: str,
        invalid_json_message: str,
        json_body: object,
    ) -> object:
        return self._request_json(
            "PUT",
            session,
            url,
            unexpected_response_message=unexpected_response_message,
            invalid_json_message=invalid_json_message,
            json_body=json_body,
        )

    def post_json(
        self,
        session: AuthSession,
        url: str,
        *,
        unexpected_response_message: str,
        invalid_json_message: str,
        json_body: object,
    ) -> object:
        return self._request_json(
            "POST",
            session,
            url,
            unexpected_response_message=unexpected_response_message,
            invalid_json_message=invalid_json_message,
            json_body=json_body,
        )

    def _request_json(
        self,
        method: HttpMethod,
        session: AuthSession,
        url: str,
        *,
        unexpected_response_message: str,
        invalid_json_message: str,
        params: QueryParams | None = None,
        json_body: object | None = None,
    ) -> object:
        headers = self.build_headers(session)

        try:
            if method == "GET":
                response = httpx.get(url, headers=headers, params=params, timeout=30.0)
            elif method == "PUT":
                response = httpx.put(url, headers=headers, json=json_body, timeout=30.0)
            else:
                response = httpx.post(url, headers=headers, json=json_body, timeout=30.0)
        except httpx.HTTPError as exc:
            raise AuthenticationError(f"Request to TU Delft portal failed: {exc}") from exc

        if response.status_code == 401:
            raise AuthenticationError("Stored session is no longer valid. Run 'tudelft login' again.")

        if response.status_code != 200:
            raise PortalChangedError(f"{unexpected_response_message}: {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            raise PortalChangedError(invalid_json_message) from exc
