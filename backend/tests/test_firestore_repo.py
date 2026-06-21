"""Integration tests for FirestoreRepository against the Firestore emulator.

These exercise the real adapter (serialization round-trips, field names, query filters) which the
unit suite — running on MemoryRepository — cannot. They are skipped unless both:

  * ``google-cloud-firestore`` is installed (``pip install -r requirements.txt``), and
  * the Firestore emulator is running and ``FIRESTORE_EMULATOR_HOST`` is set.

Run locally:

    firebase emulators:start --only firestore
    FIRESTORE_EMULATOR_HOST=localhost:8080 GCLOUD_PROJECT=demo-pfa pytest tests/test_firestore_repo.py

Note: the emulator does not enforce composite indexes, so this won't catch a missing production
index (see infra/firestore.indexes.json for those); it does catch field-name and query-shape bugs.
"""

from __future__ import annotations

import os
import uuid
from datetime import date

import pytest

pytest.importorskip("google.cloud.firestore")

pytestmark = pytest.mark.skipif(
    not os.environ.get("FIRESTORE_EMULATOR_HOST"),
    reason="Firestore emulator not running (set FIRESTORE_EMULATOR_HOST)",
)

from app.adapters.firestore_repo import FirestoreRepository  # noqa: E402
from app.domain.categories import Category  # noqa: E402
from app.domain.models import (  # noqa: E402
    Alert,
    AlertType,
    Budget,
    Flow,
    RecurringStream,
    Severity,
    Transaction,
    TransactionSource,
    UserSettings,
)
from app.ports.repository import ItemSecret  # noqa: E402


class _IdentityCipher:
    """No-op cipher so the repo runs without KMS credentials."""

    def encrypt(self, s: str) -> str:
        return s

    def decrypt(self, s: str) -> str:
        return s


@pytest.fixture
def repo() -> FirestoreRepository:
    return FirestoreRepository(project_id="demo-pfa", cipher=_IdentityCipher())


@pytest.fixture
def uid() -> str:
    # Unique per test so the persistent emulator state never collides across tests.
    return f"u_{uuid.uuid4().hex[:10]}"


def test_item_secret_roundtrip(repo, uid):
    item_id = f"it_{uid}"
    repo.save_item_secret(ItemSecret(item_id=item_id, uid=uid, access_token="secret-xyz", cursor="c0"))

    got = repo.get_item_secret(item_id)
    assert got is not None
    assert got.access_token == "secret-xyz"
    assert got.uid == uid

    repo.update_cursor(item_id, "c1")
    assert repo.get_item_secret(item_id).cursor == "c1"


def test_transaction_roundtrip_and_queries(repo, uid):
    txn = Transaction(
        id="plaid_a", account_id="acc1", amount_cents=-1599, date=date(2026, 6, 10),
        merchant="Shell", category=Category.TRANSPORT, source=TransactionSource.PLAID,
        plaid_txn_id="a",
    )
    repo.upsert_transaction(uid, txn)

    got = repo.get_transaction(uid, "plaid_a")
    assert got.amount_cents == -1599
    assert got.category == Category.TRANSPORT       # enum round-trips
    assert got.date == date(2026, 6, 10)            # date round-trips
    assert got.source == TransactionSource.PLAID

    assert repo.get_transaction_by_plaid_id(uid, "a").id == "plaid_a"
    assert [t.id for t in repo.list_transactions(uid, category="TRANSPORT")] == ["plaid_a"]
    assert [t.id for t in repo.list_transactions(uid, account_id="acc1")] == ["plaid_a"]
    assert len(repo.get_transactions_for_month(uid, "2026-06")) == 1
    assert repo.get_transactions_for_month(uid, "2026-05") == []

    repo.delete_transaction_by_plaid_id(uid, "a")
    assert repo.get_transaction(uid, "plaid_a") is None


def test_find_candidate_duplicates(repo, uid):
    repo.upsert_transaction(
        uid,
        Transaction(id="m1", account_id="a", amount_cents=-4000, date=date(2026, 1, 10),
                    merchant="Diner", source=TransactionSource.MANUAL),
    )
    hit = repo.find_candidate_duplicates(uid, amount_cents=-4000, around=date(2026, 1, 11),
                                         window_days=3)
    assert [c.id for c in hit] == ["m1"]
    # Outside the date window -> no candidate.
    assert repo.find_candidate_duplicates(uid, amount_cents=-4000, around=date(2026, 2, 1),
                                          window_days=3) == []


def test_merchant_and_rapid_repeat_queries(repo, uid):
    repo.upsert_transaction(
        uid,
        Transaction(id="x1", account_id="a", amount_cents=-2500, date=date(2026, 6, 10),
                    merchant="Shop", source=TransactionSource.PLAID),
    )
    assert repo.has_other_transaction_with_merchant(uid, "Shop", "other") is True
    assert repo.has_other_transaction_with_merchant(uid, "Shop", "x1") is False

    repo.upsert_transaction(
        uid,
        Transaction(id="x2", account_id="a", amount_cents=-2500, date=date(2026, 6, 10),
                    merchant="Shop", source=TransactionSource.PLAID),
    )
    assert repo.count_same_merchant_amount_on_date(
        uid, merchant="Shop", amount_cents=-2500, on=date(2026, 6, 10), exclude_id="x2"
    ) == 1


def test_budget_roundtrip(repo, uid):
    repo.upsert_budget(uid, Budget(month="2026-06", caps_cents={"GROCERIES": 40000},
                                   spent_cents={"GROCERIES": 2500}))
    b = repo.get_budget(uid, "2026-06")
    assert b.caps_cents["GROCERIES"] == 40000
    assert b.spent_cents["GROCERIES"] == 2500
    assert repo.get_budget(uid, "2026-05") is None


def test_alerts_roundtrip_and_unread_filter(repo, uid):
    repo.add_alert(uid, Alert(id="al1", type=AlertType.LARGE_TRANSACTION,
                              severity=Severity.WARNING, title="Large", message="m"))
    assert repo.get_alert(uid, "al1").title == "Large"
    assert len(repo.list_alerts(uid, unread_only=True)) == 1

    repo.mark_alert_read(uid, "al1")
    assert repo.get_alert(uid, "al1").read is True
    assert repo.list_alerts(uid, unread_only=True) == []


def test_settings_roundtrip(repo, uid):
    assert repo.get_settings(uid) is None
    repo.save_settings(uid, UserSettings(large_txn_threshold_cents=10000, fcm_tokens=["d1"]))
    s = repo.get_settings(uid)
    assert s.large_txn_threshold_cents == 10000
    assert s.fcm_tokens == ["d1"]


def test_rollups_roundtrip_and_kind_filter(repo, uid):
    repo.upsert_rollup(uid, "networth_2026-06-10",
                       {"kind": "netWorthSnapshot", "period": "2026-06-10",
                        "data": {"net_cents": 100}})
    repo.upsert_rollup(uid, "monthcat_2026-06",
                       {"kind": "monthlyByCategory", "period": "2026-06", "data": {}})
    snaps = repo.list_rollups(uid, kind="netWorthSnapshot")
    assert len(snaps) == 1
    assert snaps[0]["period"] == "2026-06-10"


def test_recurring_roundtrip(repo, uid):
    repo.upsert_recurring(
        uid,
        RecurringStream(id="s1", merchant="Netflix", frequency="MONTHLY", flow=Flow.OUTFLOW,
                        average_amount_cents=-1599, last_date=date(2026, 6, 1)),
    )
    got = repo.get_recurring_stream(uid, "s1")
    assert got.merchant == "Netflix"
    assert got.flow == Flow.OUTFLOW
    assert got.last_date == date(2026, 6, 1)
    assert any(s.id == "s1" for s in repo.get_recurring_streams(uid))
