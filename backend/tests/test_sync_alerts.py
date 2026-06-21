from app.adapters.fake_provider import FakeBankProvider, plaid_txn
from app.adapters.memory_repo import MemoryRepository
from app.adapters.notifier import FakeNotifier
from app.domain.models import PlaidItem
from app.ports.bank_provider import ProviderSyncResult
from app.ports.repository import ItemSecret
from app.services.alerts import AlertEngine
from app.services.budgets import BudgetService
from app.services.rollups import RollupService
from app.services.sync import SyncService


def _service(repo, notifier, pages, cursor=None):
    repo.save_item_secret(ItemSecret(item_id="item_1", uid="u1", access_token="x", cursor=cursor))
    repo.upsert_item("u1", PlaidItem(id="item_1"))
    return SyncService(
        FakeBankProvider(pages=pages),
        repo,
        alert_engine=AlertEngine(repo, notifier),
        budget_service=BudgetService(repo),
        rollup_service=RollupService(repo),
    )


def test_initial_backfill_suppresses_alerts():
    repo, notifier = MemoryRepository(), FakeNotifier()
    page = ProviderSyncResult(
        added=[
            plaid_txn(transaction_id="t1", amount=600.0, merchant_name="Big Store",
                      pfc_primary="GENERAL_MERCHANDISE", date="2026-06-10")
        ],
        next_cursor="c1",
    )
    report = _service(repo, notifier, [page], cursor=None).sync_item("u1", "item_1")

    assert report.is_initial is True
    assert report.alerts_created == 0
    assert notifier.sent == []
    # Budget/rollup still computed during backfill.
    assert repo.get_budget("u1", "2026-06").spent_cents.get("SHOPPING") == 60000


def test_incremental_sync_creates_and_notifies_alerts():
    repo, notifier = MemoryRepository(), FakeNotifier()
    page = ProviderSyncResult(
        added=[
            plaid_txn(transaction_id="t1", amount=600.0, merchant_name="Big Store",
                      pfc_primary="GENERAL_MERCHANDISE", date="2026-06-10")
        ],
        next_cursor="c2",
    )
    report = _service(repo, notifier, [page], cursor="prev-cursor").sync_item("u1", "item_1")

    assert report.is_initial is False
    assert report.alerts_created >= 1  # large transaction + new merchant
    assert len(notifier.sent) == report.alerts_created
    assert len(repo.list_alerts("u1")) == report.alerts_created
