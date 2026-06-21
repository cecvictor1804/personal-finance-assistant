"""Datastore port. FirestoreRepository is the concrete adapter; tests use MemoryRepository.

Method names mirror how services use them. Plaid access tokens/cursors live in a separate,
client-inaccessible store (`plaid_secrets`); they are exposed here only to backend code.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from app.domain.models import (
    Account,
    Alert,
    Budget,
    ItemStatus,
    PlaidItem,
    Receipt,
    RecurringStream,
    Rule,
    Transaction,
    UserSettings,
)


class ItemSecret:
    """Decrypted Plaid credentials for one item (never leaves the backend)."""

    def __init__(self, item_id: str, uid: str, access_token: str, cursor: str | None = None):
        self.item_id = item_id
        self.uid = uid
        self.access_token = access_token
        self.cursor = cursor


class Repository(Protocol):
    # --- Plaid item secrets (client-inaccessible) ---
    def save_item_secret(self, secret: ItemSecret) -> None: ...
    def get_item_secret(self, item_id: str) -> ItemSecret | None: ...
    def update_cursor(self, item_id: str, cursor: str) -> None: ...

    # --- Plaid item metadata (client-readable) ---
    def upsert_item(self, uid: str, item: PlaidItem) -> None: ...
    def get_items(self, uid: str) -> list[PlaidItem]: ...
    def set_item_status(self, uid: str, item_id: str, status: ItemStatus) -> None: ...
    def touch_item_synced(self, uid: str, item_id: str) -> None: ...

    # --- Accounts ---
    def upsert_account(self, uid: str, account: Account) -> None: ...
    def get_accounts(self, uid: str) -> list[Account]: ...

    # --- Transactions ---
    def upsert_transaction(self, uid: str, txn: Transaction) -> None: ...
    def get_transaction(self, uid: str, txn_id: str) -> Transaction | None: ...
    def get_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> Transaction | None: ...
    def delete_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> None: ...
    def list_transactions(
        self,
        uid: str,
        *,
        limit: int = 50,
        start_date: date | None = None,
        end_date: date | None = None,
        category: str | None = None,
        account_id: str | None = None,
    ) -> list[Transaction]: ...

    def find_candidate_duplicates(
        self, uid: str, *, amount_cents: int, around: date, window_days: int
    ) -> list[Transaction]:
        """Return manual transactions near `around` with the same amount (dedup candidates)."""
        ...

    def find_transactions_by_amount(
        self, uid: str, *, amount_cents: int, around: date, window_days: int
    ) -> list[Transaction]:
        """Return transactions of ANY source near `around` with the same amount (receipt match)."""
        ...

    def get_transactions_for_month(self, uid: str, month: str) -> list[Transaction]:
        """All transactions in a "YYYY-MM" month (for budget/rollup recompute)."""
        ...

    def has_other_transaction_with_merchant(
        self, uid: str, merchant: str, exclude_id: str
    ) -> bool:
        """True if any other transaction shares this merchant (drives the new-merchant alert)."""
        ...

    def count_same_merchant_amount_on_date(
        self, uid: str, *, merchant: str, amount_cents: int, on: date, exclude_id: str
    ) -> int:
        """Count same-merchant, same-amount transactions on a date (rapid-repeat / double charge)."""
        ...

    # --- Rules ---
    def get_rules(self, uid: str) -> list[Rule]: ...
    def add_rule(self, uid: str, rule: Rule) -> None: ...
    def delete_rule(self, uid: str, rule_id: str) -> None: ...

    # --- Budgets ---
    def get_budget(self, uid: str, month: str) -> Budget | None: ...
    def upsert_budget(self, uid: str, budget: Budget) -> None: ...

    # --- Alerts ---
    def add_alert(self, uid: str, alert: Alert) -> None: ...
    def get_alert(self, uid: str, alert_id: str) -> Alert | None: ...
    def list_alerts(self, uid: str, *, limit: int = 50, unread_only: bool = False) -> list[Alert]: ...
    def mark_alert_read(self, uid: str, alert_id: str) -> None: ...

    # --- Settings ---
    def get_settings(self, uid: str) -> UserSettings | None: ...
    def save_settings(self, uid: str, settings: UserSettings) -> None: ...

    # --- Rollups (precomputed aggregates; freeform docs keyed by id) ---
    def upsert_rollup(self, uid: str, rollup_id: str, doc: dict) -> None: ...
    def list_rollups(self, uid: str, *, kind: str | None = None, limit: int = 90) -> list[dict]: ...

    # --- Recurring streams ---
    def upsert_recurring(self, uid: str, stream: RecurringStream) -> None: ...
    def get_recurring_streams(self, uid: str) -> list[RecurringStream]: ...
    def get_recurring_stream(self, uid: str, stream_id: str) -> RecurringStream | None: ...

    # --- Receipts ---
    def upsert_receipt(self, uid: str, receipt: Receipt) -> None: ...
    def get_receipt(self, uid: str, receipt_id: str) -> Receipt | None: ...
    def list_receipts(self, uid: str, *, limit: int = 50) -> list[Receipt]: ...
