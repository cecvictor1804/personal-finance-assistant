from datetime import date

from app.adapters.memory_repo import MemoryRepository
from app.adapters.notifier import FakeNotifier
from app.domain.categories import Category
from app.domain.models import (
    AlertType,
    Budget,
    Transaction,
    TransactionSource,
    UserSettings,
)
from app.services.alerts import AlertEngine

UID = "u1"


def _engine():
    repo = MemoryRepository()
    notifier = FakeNotifier()
    return repo, notifier, AlertEngine(repo, notifier)


def _txn(tid="t1", cents=-1000, merchant="Cafe", d=date(2026, 6, 10), country="US"):
    return Transaction(
        id=tid,
        account_id="a1",
        amount_cents=cents,
        date=d,
        merchant=merchant,
        category=Category.FOOD_DINING,
        country=country,
        source=TransactionSource.PLAID,
    )


def _types(alerts):
    return {a.type for a in alerts}


def test_large_transaction_alert():
    repo, _, engine = _engine()
    txn = _txn(cents=-60000)  # $600 > default $500 threshold
    repo.upsert_transaction(UID, txn)
    alerts = engine.evaluate_transaction(UID, txn)
    assert AlertType.LARGE_TRANSACTION in _types(alerts)


def test_no_large_alert_below_threshold():
    repo, _, engine = _engine()
    txn = _txn(cents=-4000)
    repo.upsert_transaction(UID, txn)
    assert AlertType.LARGE_TRANSACTION not in _types(engine.evaluate_transaction(UID, txn))


def test_foreign_transaction_alert():
    repo, _, engine = _engine()
    txn = _txn(country="GB")
    repo.upsert_transaction(UID, txn)
    assert AlertType.FOREIGN_TRANSACTION in _types(engine.evaluate_transaction(UID, txn))


def test_new_merchant_then_not_new():
    repo, _, engine = _engine()
    first = _txn(tid="t1", merchant="Blue Bottle")
    repo.upsert_transaction(UID, first)
    assert AlertType.NEW_MERCHANT in _types(engine.evaluate_transaction(UID, first))

    second = _txn(tid="t2", merchant="Blue Bottle", d=date(2026, 6, 12))
    repo.upsert_transaction(UID, second)
    assert AlertType.NEW_MERCHANT not in _types(engine.evaluate_transaction(UID, second))


def test_rapid_repeat_double_charge():
    repo, _, engine = _engine()
    a = _txn(tid="t1", cents=-2500, merchant="Shop", d=date(2026, 6, 10))
    b = _txn(tid="t2", cents=-2500, merchant="Shop", d=date(2026, 6, 10))
    repo.upsert_transaction(UID, a)
    repo.upsert_transaction(UID, b)
    assert AlertType.RAPID_REPEAT in _types(engine.evaluate_transaction(UID, b))


def test_idempotent_and_notifies():
    repo, notifier, engine = _engine()
    txn = _txn(cents=-60000, merchant="Big Store")
    repo.upsert_transaction(UID, txn)

    first = engine.evaluate_transaction(UID, txn)
    assert len(first) >= 1
    notified = len(notifier.sent)
    assert notified == len(first)  # one notification per created alert

    # Re-evaluating the same transaction creates nothing new and sends nothing more.
    second = engine.evaluate_transaction(UID, txn)
    assert second == []
    assert len(notifier.sent) == notified


def test_budget_warning_and_exceeded():
    repo, _, engine = _engine()
    warn = Budget(month="2026-06", caps_cents={"GROCERIES": 10000}, spent_cents={"GROCERIES": 8500})
    assert AlertType.BUDGET_WARNING in _types(engine.evaluate_budget(UID, warn))

    repo2, _, engine2 = _engine()
    over = Budget(month="2026-06", caps_cents={"GROCERIES": 10000}, spent_cents={"GROCERIES": 12000})
    assert AlertType.BUDGET_EXCEEDED in _types(engine2.evaluate_budget(UID, over))


def test_budget_no_alert_when_under_warn():
    _, _, engine = _engine()
    under = Budget(month="2026-06", caps_cents={"GROCERIES": 10000}, spent_cents={"GROCERIES": 2000})
    assert engine.evaluate_budget(UID, under) == []


def test_respects_custom_threshold_from_settings():
    repo, _, engine = _engine()
    repo.save_settings(UID, UserSettings(large_txn_threshold_cents=2000))
    txn = _txn(cents=-2500, merchant="Mid")
    repo.upsert_transaction(UID, txn)
    assert AlertType.LARGE_TRANSACTION in _types(engine.evaluate_transaction(UID, txn))
