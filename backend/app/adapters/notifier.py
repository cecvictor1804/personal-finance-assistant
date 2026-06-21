"""Notifier adapters.

- ``FirestoreFcmNotifier``: sends FCM push to the user's registered tokens and writes an email
  document to the ``mail`` collection (consumed by the Firebase "Trigger Email" extension).
- ``FakeNotifier``: records deliveries for tests.

Delivery is best-effort: failures are swallowed so a flaky push/email never breaks a sync.
"""

from __future__ import annotations

from app.domain.models import Alert, UserSettings


class FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[tuple[str, Alert]] = []

    def notify(self, uid: str, alert: Alert, settings: UserSettings) -> None:
        self.sent.append((uid, alert))


class FirestoreFcmNotifier:
    def __init__(self) -> None:
        import firebase_admin
        from firebase_admin import firestore

        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        self._db = firestore.client()

    def notify(self, uid: str, alert: Alert, settings: UserSettings) -> None:
        self._send_push(settings.fcm_tokens, alert)
        if settings.email:
            self._send_email(settings.email, alert)

    def _send_push(self, tokens: list[str], alert: Alert) -> None:
        if not tokens:
            return
        try:
            from firebase_admin import messaging

            message = messaging.MulticastMessage(
                tokens=tokens,
                notification=messaging.Notification(title=alert.title, body=alert.message),
                data={"alert_id": alert.id, "type": alert.type.value},
            )
            messaging.send_each_for_multicast(message)
        except Exception:  # noqa: BLE001 - best-effort; never break the caller
            pass

    def _send_email(self, to: str, alert: Alert) -> None:
        try:
            self._db.collection("mail").add(
                {
                    "to": to,
                    "message": {
                        "subject": f"[Finance] {alert.title}",
                        "html": f"<p>{alert.message}</p>",
                    },
                }
            )
        except Exception:  # noqa: BLE001
            pass
