"""Recurring-stream refresh: pull Plaid recurring transactions, store them, and alert on changes.

Detects newly discovered subscriptions/bills and meaningful amount changes (e.g. a price hike on a
subscription). Like per-transaction alerts, recurring alerts are suppressed during the initial
backfill so first-link doesn't announce every existing subscription.
"""

from __future__ import annotations

from app.domain.money import format_cents
from app.domain.models import Alert, AlertType, RecurringStream, Severity
from app.ports.bank_provider import BankProvider
from app.ports.repository import Repository
from app.services.alerts import AlertEngine
from app.services.normalize import normalize_recurring


def _is_significant_change(new_cents: int, old_cents: int) -> bool:
    if old_cents == 0:
        return False
    delta = abs(new_cents - old_cents)
    return delta >= 100 and delta >= abs(old_cents) * 0.1  # >= $1 and >= 10%


class RecurringService:
    def __init__(
        self,
        provider: BankProvider,
        repo: Repository,
        alert_engine: AlertEngine | None = None,
    ) -> None:
        self._provider = provider
        self._repo = repo
        self._alert_engine = alert_engine

    def refresh_item(self, uid: str, item_id: str, *, is_initial: bool = False) -> list[Alert]:
        secret = self._repo.get_item_secret(item_id)
        if secret is None:
            return []

        created: list[Alert] = []
        for raw in self._provider.get_recurring(secret.access_token):
            stream = normalize_recurring(raw)
            existing = self._repo.get_recurring_stream(uid, stream.id)
            alert = self._diff_alert(existing, stream)
            self._repo.upsert_recurring(uid, stream)
            if alert and self._alert_engine and not is_initial and self._alert_engine.emit(uid, alert):
                created.append(alert)
        return created

    def refresh_all(self, uid: str, *, is_initial: bool = False) -> list[Alert]:
        created: list[Alert] = []
        for item in self._repo.get_items(uid):
            created.extend(self.refresh_item(uid, item.id, is_initial=is_initial))
        return created

    def _diff_alert(
        self, existing: RecurringStream | None, stream: RecurringStream
    ) -> Alert | None:
        amount = format_cents(abs(stream.average_amount_cents))
        merchant = stream.merchant or "a merchant"
        freq = stream.frequency.lower()

        if existing is None:
            if not stream.is_active:
                return None
            return Alert(
                id=f"newrecurring_{stream.id}",
                type=AlertType.NEW_RECURRING,
                severity=Severity.INFO,
                title="New recurring charge",
                message=f"Detected a {freq} {stream.flow.value} of {amount} at {merchant}.",
                category=stream.category,
                amount_cents=stream.average_amount_cents,
            )

        if _is_significant_change(stream.average_amount_cents, existing.average_amount_cents):
            old = format_cents(abs(existing.average_amount_cents))
            return Alert(
                # last_date in the id so a later change on a new date is a distinct alert.
                id=f"recurringchange_{stream.id}_{stream.last_date}",
                type=AlertType.RECURRING_AMOUNT_CHANGE,
                severity=Severity.WARNING,
                title="Recurring amount changed",
                message=f"{merchant} changed from {old} to {amount}.",
                category=stream.category,
                amount_cents=stream.average_amount_cents,
            )
        return None
