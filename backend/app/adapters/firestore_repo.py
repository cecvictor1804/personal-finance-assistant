"""Firestore implementation of the Repository port (Admin SDK / google-cloud-firestore).

Documents store the pydantic models' JSON form (snake_case keys, dates/datetimes as ISO strings,
enums as their values), which round-trips cleanly back through the models. Plaid access tokens are
KMS-encrypted and live in the top-level, client-inaccessible `plaid_secrets` collection.

Imported lazily by the composition root; not exercised by unit tests (use MemoryRepository there).
"""

from __future__ import annotations

from datetime import date

from app.adapters.crypto import KmsCipher
from app.domain.models import (
    Account,
    Alert,
    Budget,
    ItemStatus,
    PlaidItem,
    RecurringStream,
    Rule,
    Transaction,
    UserSettings,
    utcnow,
)
from app.ports.repository import ItemSecret


class FirestoreRepository:
    def __init__(self, project_id: str, kms_key_name: str) -> None:
        from google.cloud import firestore

        self._db = firestore.Client(project=project_id)
        self._cipher = KmsCipher(kms_key_name)

    # --- path helpers ---
    def _user(self, uid: str):
        return self._db.collection("users").document(uid)

    def _txns(self, uid: str):
        return self._user(uid).collection("transactions")

    # --- secrets (top-level, client-inaccessible) ---
    def save_item_secret(self, secret: ItemSecret) -> None:
        self._db.collection("plaid_secrets").document(secret.item_id).set(
            {
                "uid": secret.uid,
                "accessTokenEnc": self._cipher.encrypt(secret.access_token),
                "cursor": secret.cursor,
            }
        )

    def get_item_secret(self, item_id: str) -> ItemSecret | None:
        snap = self._db.collection("plaid_secrets").document(item_id).get()
        if not snap.exists:
            return None
        d = snap.to_dict()
        return ItemSecret(
            item_id=item_id,
            uid=d["uid"],
            access_token=self._cipher.decrypt(d["accessTokenEnc"]),
            cursor=d.get("cursor"),
        )

    def update_cursor(self, item_id: str, cursor: str) -> None:
        self._db.collection("plaid_secrets").document(item_id).update({"cursor": cursor})

    # --- items ---
    def upsert_item(self, uid: str, item: PlaidItem) -> None:
        self._user(uid).collection("items").document(item.id).set(item.model_dump(mode="json"))

    def get_items(self, uid: str) -> list[PlaidItem]:
        return [PlaidItem(**s.to_dict()) for s in self._user(uid).collection("items").stream()]

    def set_item_status(self, uid: str, item_id: str, status: ItemStatus) -> None:
        self._user(uid).collection("items").document(item_id).update({"status": status.value})

    def touch_item_synced(self, uid: str, item_id: str) -> None:
        self._user(uid).collection("items").document(item_id).update(
            {"last_sync_at": utcnow().isoformat()}
        )

    # --- accounts ---
    def upsert_account(self, uid: str, account: Account) -> None:
        self._user(uid).collection("accounts").document(account.id).set(
            account.model_dump(mode="json")
        )

    def get_accounts(self, uid: str) -> list[Account]:
        return [Account(**s.to_dict()) for s in self._user(uid).collection("accounts").stream()]

    # --- transactions ---
    def upsert_transaction(self, uid: str, txn: Transaction) -> None:
        self._txns(uid).document(txn.id).set(txn.model_dump(mode="json"))

    def get_transaction(self, uid: str, txn_id: str) -> Transaction | None:
        snap = self._txns(uid).document(txn_id).get()
        return Transaction(**snap.to_dict()) if snap.exists else None

    def get_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> Transaction | None:
        q = self._txns(uid).where("plaid_txn_id", "==", plaid_txn_id).limit(1).stream()
        for s in q:
            return Transaction(**s.to_dict())
        return None

    def delete_transaction_by_plaid_id(self, uid: str, plaid_txn_id: str) -> None:
        q = self._txns(uid).where("plaid_txn_id", "==", plaid_txn_id).limit(1).stream()
        for s in q:
            s.reference.delete()

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
        from google.cloud.firestore import Query

        q = self._txns(uid)
        if category:
            q = q.where("category", "==", category)
        if account_id:
            q = q.where("account_id", "==", account_id)
        if start_date:
            q = q.where("date", ">=", start_date.isoformat())
        if end_date:
            q = q.where("date", "<=", end_date.isoformat())
        q = q.order_by("date", direction=Query.DESCENDING).limit(limit)
        return [Transaction(**s.to_dict()) for s in q.stream()]

    def find_candidate_duplicates(
        self, uid: str, *, amount_cents: int, around: date, window_days: int
    ) -> list[Transaction]:
        from datetime import timedelta

        lo, hi = around - timedelta(days=window_days), around + timedelta(days=window_days)
        q = (
            self._txns(uid)
            .where("source", "==", "manual")
            .where("amount_cents", "==", amount_cents)
            .where("date", ">=", lo.isoformat())
            .where("date", "<=", hi.isoformat())
        )
        return [Transaction(**s.to_dict()) for s in q.stream()]

    def get_transactions_for_month(self, uid: str, month: str) -> list[Transaction]:
        q = (
            self._txns(uid)
            .where("date", ">=", f"{month}-01")
            .where("date", "<=", f"{month}-31")
        )
        return [Transaction(**s.to_dict()) for s in q.stream()]

    def has_other_transaction_with_merchant(
        self, uid: str, merchant: str, exclude_id: str
    ) -> bool:
        q = self._txns(uid).where("merchant", "==", merchant).limit(2).stream()
        return any(s.id != exclude_id for s in q)

    def count_same_merchant_amount_on_date(
        self, uid: str, *, merchant: str, amount_cents: int, on: date, exclude_id: str
    ) -> int:
        q = (
            self._txns(uid)
            .where("merchant", "==", merchant)
            .where("amount_cents", "==", amount_cents)
            .where("date", "==", on.isoformat())
            .stream()
        )
        return sum(1 for s in q if s.id != exclude_id)

    # --- rules ---
    def get_rules(self, uid: str) -> list[Rule]:
        return [Rule(**s.to_dict()) for s in self._user(uid).collection("rules").stream()]

    def add_rule(self, uid: str, rule: Rule) -> None:
        self._user(uid).collection("rules").document(rule.id).set(rule.model_dump(mode="json"))

    def delete_rule(self, uid: str, rule_id: str) -> None:
        self._user(uid).collection("rules").document(rule_id).delete()

    # --- budgets ---
    def get_budget(self, uid: str, month: str) -> Budget | None:
        snap = self._user(uid).collection("budgets").document(month).get()
        return Budget(**snap.to_dict()) if snap.exists else None

    def upsert_budget(self, uid: str, budget: Budget) -> None:
        self._user(uid).collection("budgets").document(budget.month).set(
            budget.model_dump(mode="json")
        )

    # --- alerts ---
    def add_alert(self, uid: str, alert: Alert) -> None:
        self._user(uid).collection("alerts").document(alert.id).set(alert.model_dump(mode="json"))

    def get_alert(self, uid: str, alert_id: str) -> Alert | None:
        snap = self._user(uid).collection("alerts").document(alert_id).get()
        return Alert(**snap.to_dict()) if snap.exists else None

    def list_alerts(self, uid: str, *, limit: int = 50, unread_only: bool = False) -> list[Alert]:
        from google.cloud.firestore import Query

        q = self._user(uid).collection("alerts")
        if unread_only:
            q = q.where("read", "==", False)
        q = q.order_by("created_at", direction=Query.DESCENDING).limit(limit)
        return [Alert(**s.to_dict()) for s in q.stream()]

    def mark_alert_read(self, uid: str, alert_id: str) -> None:
        self._user(uid).collection("alerts").document(alert_id).update({"read": True})

    # --- settings ---
    def get_settings(self, uid: str) -> UserSettings | None:
        snap = self._user(uid).collection("meta").document("settings").get()
        return UserSettings(**snap.to_dict()) if snap.exists else None

    def save_settings(self, uid: str, settings: UserSettings) -> None:
        self._user(uid).collection("meta").document("settings").set(settings.model_dump(mode="json"))

    # --- rollups ---
    def upsert_rollup(self, uid: str, rollup_id: str, doc: dict) -> None:
        self._user(uid).collection("rollups").document(rollup_id).set(doc)

    def list_rollups(self, uid: str, *, kind: str | None = None, limit: int = 90) -> list[dict]:
        from google.cloud.firestore import Query

        q = self._user(uid).collection("rollups")
        if kind:
            q = q.where("kind", "==", kind)
        q = q.order_by("period", direction=Query.DESCENDING).limit(limit)
        return [s.to_dict() for s in q.stream()]

    # --- recurring ---
    def upsert_recurring(self, uid: str, stream: RecurringStream) -> None:
        self._user(uid).collection("recurring").document(stream.id).set(
            stream.model_dump(mode="json")
        )

    def get_recurring_streams(self, uid: str) -> list[RecurringStream]:
        return [
            RecurringStream(**s.to_dict())
            for s in self._user(uid).collection("recurring").stream()
        ]

    def get_recurring_stream(self, uid: str, stream_id: str) -> RecurringStream | None:
        snap = self._user(uid).collection("recurring").document(stream_id).get()
        return RecurringStream(**snap.to_dict()) if snap.exists else None
