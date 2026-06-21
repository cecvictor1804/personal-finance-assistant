from app.adapters.fake_provider import FakeBankProvider, plaid_recurring
from app.adapters.memory_repo import MemoryRepository
from app.adapters.notifier import FakeNotifier
from app.domain.categories import Category
from app.domain.models import AlertType, Flow, PlaidItem
from app.ports.repository import ItemSecret
from app.services.alerts import AlertEngine
from app.services.normalize import normalize_recurring
from app.services.recurring import RecurringService

UID = "u1"


def _repo_with_item() -> MemoryRepository:
    repo = MemoryRepository()
    repo.save_item_secret(ItemSecret(item_id="item_1", uid=UID, access_token="x"))
    repo.upsert_item(UID, PlaidItem(id="item_1"))
    return repo


def _service(repo, notifier, streams) -> RecurringService:
    provider = FakeBankProvider(recurring=streams)
    return RecurringService(provider, repo, alert_engine=AlertEngine(repo, notifier))


def test_normalize_recurring_sign_flow_and_category():
    out = normalize_recurring(
        plaid_recurring(stream_id="s1", merchant_name="Netflix", average_amount=15.99,
                        flow="outflow", frequency="MONTHLY", last_date="2026-05-03",
                        pfc_primary="ENTERTAINMENT")
    )
    assert out.flow == Flow.OUTFLOW
    assert out.average_amount_cents == -1599
    assert out.frequency == "MONTHLY"
    assert out.category == Category.ENTERTAINMENT

    inn = normalize_recurring(
        plaid_recurring(stream_id="s2", merchant_name="Payroll", average_amount=3000.00,
                        flow="inflow", frequency="BIWEEKLY")
    )
    assert inn.flow == Flow.INFLOW
    assert inn.average_amount_cents == 300000


def test_refresh_new_stream_alerts_when_not_initial():
    repo, notifier = _repo_with_item(), FakeNotifier()
    svc = _service(repo, notifier, [plaid_recurring(stream_id="s1", merchant_name="Netflix",
                                                    average_amount=15.99)])
    created = svc.refresh_item(UID, "item_1", is_initial=False)

    assert [a.type for a in created] == [AlertType.NEW_RECURRING]
    assert repo.get_recurring_stream(UID, "s1") is not None
    assert len(notifier.sent) == 1


def test_refresh_initial_stores_without_alerting():
    repo, notifier = _repo_with_item(), FakeNotifier()
    svc = _service(repo, notifier, [plaid_recurring(stream_id="s1", merchant_name="Netflix",
                                                    average_amount=15.99)])
    created = svc.refresh_item(UID, "item_1", is_initial=True)

    assert created == []
    assert repo.get_recurring_stream(UID, "s1") is not None
    assert notifier.sent == []


def test_refresh_detects_significant_amount_change():
    repo, notifier = _repo_with_item(), FakeNotifier()
    _service(repo, notifier, [plaid_recurring(stream_id="s1", merchant_name="Netflix",
                                              average_amount=15.99, last_date="2026-05-03")]
             ).refresh_item(UID, "item_1", is_initial=True)

    created = _service(
        repo, notifier,
        [plaid_recurring(stream_id="s1", merchant_name="Netflix", average_amount=19.99,
                         last_date="2026-06-03")],
    ).refresh_item(UID, "item_1", is_initial=False)

    assert [a.type for a in created] == [AlertType.RECURRING_AMOUNT_CHANGE]


def test_refresh_ignores_small_amount_change():
    repo, notifier = _repo_with_item(), FakeNotifier()
    _service(repo, notifier, [plaid_recurring(stream_id="s1", average_amount=15.99,
                                              last_date="2026-05-03")]
             ).refresh_item(UID, "item_1", is_initial=True)

    created = _service(
        repo, notifier,
        [plaid_recurring(stream_id="s1", average_amount=16.20, last_date="2026-06-03")],
    ).refresh_item(UID, "item_1", is_initial=False)

    assert created == []
