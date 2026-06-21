"""In-memory Repository implementation.

Used by the test suite and as a zero-dependency local backend. Mirrors the Firestore adapter's
behavior closely enough that services behave identically against either.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

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
    TransactionSource,
    UserSettings,
    utcnow,
)
from app.ports.repository import ItemSecret


class MemoryRepository:
    def __init__(self) -> None:
        self._secrets: dict[str, ItemSecret] = {}
        self._items: dict[str, dict[str, PlaidItem]] = defaultdict(dict)
        self._accounts: dict[str, dict[str, Account]] = defaultdict(dict)
        self._txns: dict[str, dict[str, Transaction]] = defaultdict(dict)
        self._rules: dict[str, dict[str, Rule]] = defaultdict(dict)
        self._budgets: dict[str, dict[str, Budget]] = defaultdict(dict)
        self._alerts: dict[str, dict[str, Alert]] = defaultdict(dict)
        self._settings: dict[str, UserSettings] = {}
        self._rollups: dict[str, dict[str, dict]] = defaultdict(dict)
        self._recurring: dict[str, dict[str, RecurringStream]] = defaultdict(dict)
        self._receipts: dict[str, dict[str, Receipt]] = defaultdict(dict)

    # --- secrets ---
    def save_item_secret(self, secret: ItemSecret) -> None:
        self._secrets[secret.item_id] = secret

    def get_item_secret(self, item_id: str) -> ItemSecret | None:
        return self._secrets.get(item_id)

    def update_cursor(self, item_id: str, cursor: str) -> None:
        if item_id in self._secrets:
            self._secrets[item_id].cursor = cursor

    # --- items ---
    def upsert_item(self, uid: str, item: PlaidItem) -> None:
        self._items[uid][item.id] = item

    def get_items(self, uid: str) -> list[PlaidItem]:
        return list(self._items[uid].values())

    def set_item_status(self, uid: str, item_id: str, status: ItemStatus) -> None:
        item = self._items[uid].get(item_id)
        if item:
            item.status = status

    def touch_item_synced(self, uid: str, item_id: str) -> None:
        item = self._items[uid].get(item_id)
        if item:
            item.last_sync_at = utcnow()

    # --- accounts ---
    def upsert_account(self, uid: str, account: Account) -> None:
        self._accounts[uid][account.id] = account

    def get_accounts(self, uid: str) -> list[Account]:
        return list(self._accounts[uid].values())

    # --- transactions ---
    def upsert_transaction(self, uid: str, txn: Transaction) -> None:
        self._txns[uid][txn.id] = txn

    def get_transaction(self, uid: str, txn_id: str) -> Transaction | None:
        return self._txns[uid].get(txn_id)

    def get_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> Transaction | None:
        for t in self._txns[uid].values():
            if t.plaid_txn_id == plaid_txn_id:
                return t
        return None

    def delete_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> None:
        existing = self.get_transaction_by_plaid_id(uid, plaid_txn_id)
        if existing:
            self._txns[uid].pop(existing.id, None)

    def list_transactions(
        self,
        uid: str,
        *,
        limit: int = 50,
        start_date: date | None = None,
        end_date: date | None = None,
        category: str | None = None,
        account_id: str | None = None,
    ) -> list[Transaction]:
        items = list(self._txns[uid].values())
        if start_date:
            items = [t for t in items if t.date >= start_date]
        if end_date:
            items = [t for t in items if t.date <= end_date]
        if category:
            items = [t for t in items if t.category.value == category]
        if account_id:
            items = [t for t in items if t.account_id == account_id]
        items.sort(key=lambda t: (t.date, t.created_at), reverse=True)
        return items[:limit]

    def find_candidate_duplicates(
        self, uid: str, *, amount_cents: int, around: date, window_days: int
    ) -> list[Transaction]:
        lo, hi = around - timedelta(days=window_days), around + timedelta(days=window_days)
        return [
            t
            for t in self._txns[uid].values()
            if t.source == TransactionSource.MANUAL
            and t.amount_cents == amount_cents
            and lo <= t.date <= hi
        ]

    def find_transactions_by_amount(
        self, uid: str, *, amount_cents: int, around: date, window_days: int
    ) -> list[Transaction]:
        lo, hi = around - timedelta(days=window_days), around + timedelta(days=window_days)
        return [
            t
            for t in self._txns[uid].values()
            if t.amount_cents == amount_cents and lo <= t.date <= hi
        ]

    def get_transactions_for_month(self, uid: str, month: str) -> list[Transaction]:
        return [t for t in self._txns[uid].values() if t.date.isoformat()[:7] == month]

    def has_other_transaction_with_merchant(
        self, uid: str, merchant: str, exclude_id: str
    ) -> bool:
        key = (merchant or "").strip().lower()
        if not key:
            return False
        return any(
            t.id != exclude_id and (t.merchant or "").strip().lower() == key
            for t in self._txns[uid].values()
        )

    def count_same_merchant_amount_on_date(
        self, uid: str, *, merchant: str, amount_cents: int, on: date, exclude_id: str
    ) -> int:
        key = (merchant or "").strip().lower()
        return sum(
            1
            for t in self._txns[uid].values()
            if t.id != exclude_id
            and t.amount_cents == amount_cents
            and t.date == on
            and (t.merchant or "").strip().lower() == key
        )

    # --- rules ---
    def get_rules(self, uid: str) -> list[Rule]:
        return list(self._rules[uid].values())

    def add_rule(self, uid: str, rule: Rule) -> None:
        self._rules[uid][rule.id] = rule

    def delete_rule(self, uid: str, rule_id: str) -> None:
        self._rules[uid].pop(rule_id, None)

    # --- budgets ---
    def get_budget(self, uid: str, month: str) -> Budget | None:
        return self._budgets[uid].get(month)

    def upsert_budget(self, uid: str, budget: Budget) -> None:
        self._budgets[uid][budget.month] = budget

    # --- alerts ---
    def add_alert(self, uid: str, alert: Alert) -> None:
        self._alerts[uid][alert.id] = alert

    def get_alert(self, uid: str, alert_id: str) -> Alert | None:
        return self._alerts[uid].get(alert_id)

    def list_alerts(self, uid: str, *, limit: int = 50, unread_only: bool = False) -> list[Alert]:
        items = list(self._alerts[uid].values())
        if unread_only:
            items = [a for a in items if not a.read]
        items.sort(key=lambda a: a.created_at, reverse=True)
        return items[:limit]

    def mark_alert_read(self, uid: str, alert_id: str) -> None:
        alert = self._alerts[uid].get(alert_id)
        if alert:
            alert.read = True

    # --- settings ---
    def get_settings(self, uid: str) -> UserSettings | None:
        return self._settings.get(uid)

    def save_settings(self, uid: str, settings: UserSettings) -> None:
        self._settings[uid] = settings

    # --- rollups ---
    def upsert_rollup(self, uid: str, rollup_id: str, doc: dict) -> None:
        self._rollups[uid][rollup_id] = doc

    def list_rollups(self, uid: str, *, kind: str | None = None, limit: int = 90) -> list[dict]:
        items = list(self._rollups[uid].values())
        if kind:
            items = [d for d in items if d.get("kind") == kind]
        items.sort(key=lambda d: d.get("period", ""), reverse=True)
        return items[:limit]

    # --- recurring ---
    def upsert_recurring(self, uid: str, stream: RecurringStream) -> None:
        self._recurring[uid][stream.id] = stream

    def get_recurring_streams(self, uid: str) -> list[RecurringStream]:
        return list(self._recurring[uid].values())

    def get_recurring_stream(self, uid: str, stream_id: str) -> RecurringStream | None:
        return self._recurring[uid].get(stream_id)

    # --- receipts ---
    def upsert_receipt(self, uid: str, receipt: Receipt) -> None:
        self._receipts[uid][receipt.id] = receipt

    def get_receipt(self, uid: str, receipt_id: str) -> Receipt | None:
        return self._receipts[uid].get(receipt_id)

    def list_receipts(self, uid: str, *, limit: int = 50) -> list[Receipt]:
        items = list(self._receipts[uid].values())
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[:limit]
