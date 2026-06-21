from datetime import date, timedelta

from app.adapters.fake_provider import FakeBankProvider, plaid_txn
from app.adapters.memory_repo import MemoryRepository
from app.adapters.notifier import FakeNotifier
from app.domain.categories import Category
from app.domain.models import (
    AlertType,
    PlaidItem,
    Transaction,
    TransactionSource,
    UserSettings,
)
from app.ports.bank_provider import ProviderSyncResult
from app.ports.repository import ItemSecret
from app.services.alerts import AlertEngine
from app.services.anomaly import (
    CategoryBaseline,
    AnomalyDetector,
    build_baselines,
    is_outlier,
)
from app.services.sync import SyncService

UID = "u1"


def _grocery(id_, cents, day):
    return Transaction(
        id=id_, account_id="a", amount_cents=cents, date=date(2026, 6, day),
        merchant="Market", category=Category.GROCERIES, source=TransactionSource.PLAID,
    )


# Eight grocery spends from $40–$60.
_HISTORY = [
    _grocery(f"h{i}", -c, i + 1)
    for i, c in enumerate([4000, 4200, 4500, 4800, 5000, 5200, 5500, 6000])
]


# --- pure statistics ---
def test_build_baselines_uses_robust_quartiles():
    baselines = build_baselines(_HISTORY)
    b = baselines[Category.GROCERIES]
    assert b.count == 8
    assert b.median == 4900.0           # mean of 4800 and 5000
    assert b.q1 == 4425.0
    assert b.q3 == 5275.0
    assert b.iqr == 850.0


def test_build_baselines_excludes_income_and_transfers():
    txns = _HISTORY + [
        Transaction(id="inc", account_id="a", amount_cents=300000, date=date(2026, 6, 1),
                    category=Category.INCOME, source=TransactionSource.PLAID),
        Transaction(id="xfer", account_id="a", amount_cents=-9999, date=date(2026, 6, 1),
                    category=Category.TRANSFER, is_transfer=True, source=TransactionSource.PLAID),
    ]
    baselines = build_baselines(txns)
    assert Category.INCOME not in baselines
    assert Category.TRANSFER not in baselines


def test_is_outlier_flags_clear_high_outlier():
    b = build_baselines(_HISTORY)[Category.GROCERIES]  # threshold = 5275 + 3*850 = 7825
    assert is_outlier(-8000, b) is True
    assert is_outlier(-6000, b) is False


def test_is_outlier_respects_cold_start_min_samples():
    b = CategoryBaseline(count=5, median=4000, q1=3000, q3=5000, iqr=2000)
    assert is_outlier(-50000, b) is False  # not enough history yet


def test_is_outlier_respects_absolute_floor():
    # Category normally ~$1.30; a $40 charge is proportionally huge but below the $50 floor.
    tiny = [_grocery(f"t{i}", -c, i + 1) for i, c in enumerate([100, 110, 120, 130, 140, 150, 160, 170])]
    b = build_baselines(tiny)[Category.GROCERIES]
    assert -4000 < -(b.q3 + 3 * b.iqr)  # would exceed the statistical fence...
    assert is_outlier(-4000, b) is False  # ...but is suppressed by the absolute floor


# --- detector ---
def _detector(repo):
    return AnomalyDetector(repo, AlertEngine(repo, FakeNotifier()))


def test_detector_flags_outlier_and_is_idempotent():
    repo = MemoryRepository()
    for t in _HISTORY:
        repo.upsert_transaction(UID, t)
    outlier = _grocery("new1", -8000, 20)
    repo.upsert_transaction(UID, outlier)  # mirrors sync (txn persisted before scoring)

    det = _detector(repo)
    created = det.evaluate(UID, [outlier])
    assert len(created) == 1
    assert created[0].type == AlertType.ANOMALOUS_SPEND
    assert created[0].txn_id == "new1"

    # Re-running creates nothing new (deterministic alert id).
    assert det.evaluate(UID, [outlier]) == []


def test_detector_ignores_normal_spend():
    repo = MemoryRepository()
    for t in _HISTORY:
        repo.upsert_transaction(UID, t)
    normal = _grocery("new2", -5100, 20)
    repo.upsert_transaction(UID, normal)
    assert _detector(repo).evaluate(UID, [normal]) == []


def test_detector_excludes_scored_txn_from_its_own_baseline():
    # Only history + the outlier exist; excluding the outlier leaves 8 samples that flag it.
    repo = MemoryRepository()
    for t in _HISTORY:
        repo.upsert_transaction(UID, t)
    outlier = _grocery("new3", -9000, 20)
    repo.upsert_transaction(UID, outlier)
    assert len(_detector(repo).evaluate(UID, [outlier])) == 1


def test_detector_respects_settings_toggle():
    repo = MemoryRepository()
    for t in _HISTORY:
        repo.upsert_transaction(UID, t)
    repo.save_settings(UID, UserSettings(anomaly_detection_enabled=False))
    outlier = _grocery("new4", -8000, 20)
    repo.upsert_transaction(UID, outlier)
    assert _detector(repo).evaluate(UID, [outlier]) == []


def test_sync_integration_flags_anomaly_on_incremental():
    repo = MemoryRepository()
    for t in _HISTORY:
        repo.upsert_transaction(UID, t)
    repo.save_item_secret(ItemSecret(item_id="item_1", uid=UID, access_token="x", cursor="prev"))
    repo.upsert_item(UID, PlaidItem(id="item_1"))

    engine = AlertEngine(repo, FakeNotifier())
    page = ProviderSyncResult(
        added=[plaid_txn(transaction_id="big", amount=80.0, merchant_name="Market",
                         pfc_primary="FOOD_AND_DRINK", pfc_detailed="FOOD_AND_DRINK_GROCERIES",
                         date="2026-06-20")],
        next_cursor="c2",
    )
    svc = SyncService(
        FakeBankProvider(pages=[page]),
        repo,
        alert_engine=engine,
        anomaly_detector=AnomalyDetector(repo, engine),
    )
    svc.sync_item(UID, "item_1")

    anomalies = [a for a in repo.list_alerts(UID) if a.type == AlertType.ANOMALOUS_SPEND]
    assert len(anomalies) == 1
    assert anomalies[0].txn_id == "plaid_big"
