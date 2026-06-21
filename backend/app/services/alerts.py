"""Alert engine (v1: explainable rules).

Per-transaction rules: large charge, brand-new merchant, foreign-country charge, and a rapid-repeat
(same merchant + amount same day = likely double charge). Budget rules: warn at a threshold,
critical when exceeded. Every alert id is deterministic so re-evaluating the same transaction or
budget never double-fires, and each newly created alert is pushed/emailed via the Notifier.
"""

from __future__ import annotations

from app.domain.categories import Category
from app.domain.models import Alert, AlertType, Budget, Severity, Transaction, UserSettings
from app.domain.money import format_cents
from app.ports.notifier import Notifier
from app.ports.repository import Repository
from app.services.budgets import is_spend


def _category_label(value: str) -> str:
    return value.replace("_", " ").title()


class AlertEngine:
    def __init__(self, repo: Repository, notifier: Notifier) -> None:
        self._repo = repo
        self._notifier = notifier

    def _settings(self, uid: str) -> UserSettings:
        return self._repo.get_settings(uid) or UserSettings()

    def emit(self, uid: str, alert: Alert) -> bool:
        """Persist + notify an externally-built alert if it's new. Returns True if created."""
        return self._persist_if_new(uid, alert, self._settings(uid))

    def evaluate_transaction(self, uid: str, txn: Transaction) -> list[Alert]:
        settings = self._settings(uid)
        created: list[Alert] = []
        for alert in self._transaction_alerts(uid, txn, settings):
            if self._persist_if_new(uid, alert, settings):
                created.append(alert)
        return created

    def evaluate_budget(self, uid: str, budget: Budget) -> list[Alert]:
        settings = self._settings(uid)
        created: list[Alert] = []
        for cat, cap in budget.caps_cents.items():
            if cap <= 0:
                continue
            spent = budget.spent_cents.get(cat, 0)
            label = _category_label(cat)
            if spent >= cap:
                alert = Alert(
                    id=f"budget_exceeded_{budget.month}_{cat}",
                    type=AlertType.BUDGET_EXCEEDED,
                    severity=Severity.CRITICAL,
                    title="Budget exceeded",
                    message=(
                        f"{label}: {format_cents(spent)} spent of the "
                        f"{format_cents(cap)} budget for {budget.month}."
                    ),
                    category=Category(cat),
                    amount_cents=spent,
                )
            elif spent * 100 >= cap * settings.budget_warn_percent:
                alert = Alert(
                    id=f"budget_warning_{budget.month}_{cat}",
                    type=AlertType.BUDGET_WARNING,
                    severity=Severity.WARNING,
                    title="Approaching budget",
                    message=(
                        f"{label}: {format_cents(spent)} of {format_cents(cap)} "
                        f"({round(spent / cap * 100)}%) for {budget.month}."
                    ),
                    category=Category(cat),
                    amount_cents=spent,
                )
            else:
                continue
            if self._persist_if_new(uid, alert, settings):
                created.append(alert)
        return created

    # --- rules ---
    def _transaction_alerts(
        self, uid: str, txn: Transaction, settings: UserSettings
    ) -> list[Alert]:
        alerts: list[Alert] = []
        spend = is_spend(txn)
        amount_str = format_cents(abs(txn.amount_cents))
        merchant = txn.merchant or "unknown merchant"

        if spend and abs(txn.amount_cents) >= settings.large_txn_threshold_cents:
            alerts.append(
                Alert(
                    id=f"large_{txn.id}",
                    type=AlertType.LARGE_TRANSACTION,
                    severity=Severity.WARNING,
                    title="Large transaction",
                    message=f"{amount_str} at {merchant}.",
                    txn_id=txn.id,
                    category=txn.category,
                    amount_cents=txn.amount_cents,
                )
            )

        if txn.country and txn.country != settings.home_country:
            alerts.append(
                Alert(
                    id=f"foreign_{txn.id}",
                    type=AlertType.FOREIGN_TRANSACTION,
                    severity=Severity.WARNING,
                    title="Foreign transaction",
                    message=f"{amount_str} charged in {txn.country} at {merchant}.",
                    txn_id=txn.id,
                    amount_cents=txn.amount_cents,
                )
            )

        if (
            spend
            and txn.merchant
            and not self._repo.has_other_transaction_with_merchant(uid, txn.merchant, txn.id)
        ):
            alerts.append(
                Alert(
                    id=f"newmerchant_{txn.id}",
                    type=AlertType.NEW_MERCHANT,
                    severity=Severity.INFO,
                    title="New merchant",
                    message=f"First charge from {txn.merchant}: {amount_str}.",
                    txn_id=txn.id,
                    amount_cents=txn.amount_cents,
                )
            )

        if (
            spend
            and txn.merchant
            and self._repo.count_same_merchant_amount_on_date(
                uid,
                merchant=txn.merchant,
                amount_cents=txn.amount_cents,
                on=txn.date,
                exclude_id=txn.id,
            )
            >= 1
        ):
            alerts.append(
                Alert(
                    id=f"rapid_{txn.id}",
                    type=AlertType.RAPID_REPEAT,
                    severity=Severity.WARNING,
                    title="Possible duplicate charge",
                    message=f"{amount_str} at {txn.merchant} appears more than once on {txn.date}.",
                    txn_id=txn.id,
                    amount_cents=txn.amount_cents,
                )
            )

        return alerts

    def _persist_if_new(self, uid: str, alert: Alert, settings: UserSettings) -> bool:
        if self._repo.get_alert(uid, alert.id) is not None:
            return False
        self._repo.add_alert(uid, alert)
        self._notifier.notify(uid, alert, settings)
        return True
