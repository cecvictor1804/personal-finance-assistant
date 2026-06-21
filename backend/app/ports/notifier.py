"""Notification port. Delivers an alert to the user via push (FCM) and/or email."""

from __future__ import annotations

from typing import Protocol

from app.domain.models import Alert, UserSettings


class Notifier(Protocol):
    def notify(self, uid: str, alert: Alert, settings: UserSettings) -> None:
        """Best-effort delivery of an alert. Implementations must not raise on delivery failure."""
        ...
