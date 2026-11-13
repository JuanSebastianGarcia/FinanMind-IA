"""Minimal Google Calendar v3 REST client for the user's primary calendar."""

from __future__ import annotations

import requests
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials


class GoogleCalendarApiError(Exception):
    """Raised when Google rejects a calendar request."""


class GoogleCalendarClient:
    """Insert, update and delete events; read the calendar time zone."""

    _BASE = "https://www.googleapis.com/calendar/v3/calendars/primary"
    _TIMEOUT = 20

    def __init__(self, credentials: Credentials) -> None:
        self._session = AuthorizedSession(credentials)

    def time_zone(self) -> str:
        """IANA time zone of the primary calendar (e.g. ``America/Bogota``)."""
        data = self._request("GET", "/events", params={"maxResults": 1})
        return data.get("timeZone") or "UTC"

    def insert_event(self, body: dict) -> str:
        return self._request("POST", "/events", json=body)["id"]

    def update_event(self, event_id: str, body: dict) -> str | None:
        """Replace an event; ``None`` when it no longer exists in the calendar."""
        data = self._request("PUT", f"/events/{event_id}", json=body, missing_ok=True)
        if data is None or data.get("status") == "cancelled":
            return None
        return data["id"]

    def delete_event(self, event_id: str) -> None:
        self._request("DELETE", f"/events/{event_id}", missing_ok=True)

    def _request(self, method: str, path: str, missing_ok: bool = False, **kwargs) -> dict | None:
        try:
            resp = self._session.request(method, self._BASE + path, timeout=self._TIMEOUT, **kwargs)
        except requests.RequestException as exc:
            raise GoogleCalendarApiError(f"No hay conexión con Google Calendar ({exc}).") from exc
        if missing_ok and resp.status_code in (404, 410):
            return None
        if resp.status_code >= 400:
            raise GoogleCalendarApiError(f"Google Calendar respondió {resp.status_code}: {self._reason(resp)}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    @classmethod
    def _reason(cls, resp: requests.Response) -> str:
        try:
            return resp.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            return resp.text[:200]
