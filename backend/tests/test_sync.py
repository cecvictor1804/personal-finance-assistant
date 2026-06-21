from datetime import date

from app.adapters.fake_provider import FakeBankProvider, plaid_account, plaid_txn
from app.adapters.memory_repo import MemoryRepository
from app.domain.categories import Category
from app.domain.models import CategorySource, PlaidItem, Transaction, TransactionSource
from app.ports.bank_provider import ProviderSyncResult
from app.ports.repository import ItemSecret
from app.services.sync import SyncService


def _service(repo: MemoryRepository, pages, accounts=None, cursor=None) -> SyncService:
    repo.save_item_secret(
        ItemSecret(item_id="item_1", uid="u1", access_token="access-x", cursor=cursor)
    )
    repo.upsert_item("u1", PlaidItem(id="item_1"))
    provider = FakeBankProvider(pages=pages, accounts=accounts or [])
    return SyncService(provider, repo)


def test_sync_adds_categorizes_and_updates_accounts(repo):
    page = ProviderSyncResult(
        added=[
            plaid_txn(
                transaction_id="t1", amount=12.00, merchant_name="Shell",
                pfc_primary="TRANSPORTATION", date="2026-01-05",
            )
        ],
        accounts=[plaid_account(account_id="acc_1", balance=500.0)],
        next_cursor="c1",
        has_more=False,
    )
    report = _service(repo, [page]).sync_item("u1", "item_1")

    assert report.added == 1
    txn = repo.get_transaction("u1", "plaid_t1")
    assert txn.amount_cents == -1200
    assert txn.category == Category.TRANSPORT
    assert txn.category_source == CategorySource.PFC
    assert repo.get_accounts("u1")[0].balance_cents == 50000
    assert repo.get_item_secret("item_1").cursor == "c1"


def test_sync_paginates_until_has_more_false(repo):
    p1 = ProviderSyncResult(added=[plaid_txn(transaction_id="t1", amount=1.0)], next_cursor="c1",
                            has_more=True)
    p2 = ProviderSyncResult(added=[plaid_txn(transaction_id="t2", amount=2.0)], next_cursor="c2",
                            has_more=False)
    report = _service(repo, [p1, p2]).sync_item("u1", "item_1")
    assert report.added == 2
    assert report.pages == 2
    assert repo.get_item_secret("item_1").cursor == "c2"


def test_sync_handles_removed(repo):
    _service(repo, [ProviderSyncResult(added=[plaid_txn(transaction_id="t1", amount=1.0)],
                                       next_cursor="c1")]).sync_item("u1", "item_1")
    assert repo.get_transaction_by_plaid_id("u1", "t1") is not None

    provider = FakeBankProvider(pages=[ProviderSyncResult(removed=["t1"], next_cursor="c2")])
    SyncService(provider, repo).sync_item("u1", "item_1")
    assert repo.get_transaction_by_plaid_id("u1", "t1") is None


def test_sync_flags_duplicate_of_manual_entry(repo):
    manual = Transaction(
        id="manual_1", account_id="acc_1", amount_cents=-4000, date=date(2026, 1, 10),
        merchant="Joe's Diner", source=TransactionSource.MANUAL,
    )
    repo.upsert_transaction("u1", manual)

    page = ProviderSyncResult(
        added=[plaid_txn(transaction_id="t1", amount=40.00, merchant_name="JOES DINER",
                         date="2026-01-11")],
        next_cursor="c1",
    )
    # Incremental sync (has a prior cursor): dedup runs. On the initial backfill it is skipped.
    report = _service(repo, [page], cursor="prev").sync_item("u1", "item_1")

    assert report.flagged_duplicates == 1
    assert repo.get_transaction("u1", "plaid_t1").possible_duplicate_of == "manual_1"


def test_initial_backfill_skips_dedup(repo):
    manual = Transaction(
        id="manual_1", account_id="acc_1", amount_cents=-4000, date=date(2026, 1, 10),
        merchant="Joe's Diner", source=TransactionSource.MANUAL,
    )
    repo.upsert_transaction("u1", manual)

    page = ProviderSyncResult(
        added=[plaid_txn(transaction_id="t1", amount=40.00, merchant_name="JOES DINER",
                         date="2026-01-11")],
        next_cursor="c1",
    )
    report = _service(repo, [page], cursor=None).sync_item("u1", "item_1")  # initial backfill

    assert report.flagged_duplicates == 0
    assert repo.get_transaction("u1", "plaid_t1").possible_duplicate_of is None


def test_modified_preserves_user_category_and_notes(repo):
    _service(
        repo,
        [ProviderSyncResult(
            added=[plaid_txn(transaction_id="t1", amount=12.0, merchant_name="Shell",
                             pfc_primary="TRANSPORTATION")],
            next_cursor="c1",
        )],
    ).sync_item("u1", "item_1")

    txn = repo.get_transaction("u1", "plaid_t1")
    txn.category = Category.GROCERIES
    txn.category_source = CategorySource.MANUAL
    txn.notes = "mistake fix"
    repo.upsert_transaction("u1", txn)

    provider = FakeBankProvider(pages=[ProviderSyncResult(
        modified=[plaid_txn(transaction_id="t1", amount=12.50, merchant_name="Shell",
                            pfc_primary="TRANSPORTATION")],
        next_cursor="c2",
    )])
    SyncService(provider, repo).sync_item("u1", "item_1")

    updated = repo.get_transaction("u1", "plaid_t1")
    assert updated.amount_cents == -1250            # amount refreshed from Plaid
    assert updated.category == Category.GROCERIES    # manual override preserved
    assert updated.category_source == CategorySource.MANUAL
    assert updated.notes == "mistake fix"            # notes preserved


def test_mark_needs_reauth(repo):
    svc = _service(repo, [])
    from app.domain.models import ItemStatus

    svc.mark_needs_reauth("u1", "item_1")
    assert repo.get_items("u1")[0].status == ItemStatus.NEEDS_REAUTH
