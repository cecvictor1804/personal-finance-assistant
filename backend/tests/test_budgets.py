from datetime import date

from app.adapters.memory_repo import MemoryRepository
from app.domain.categories import Category
from app.domain.models import Budget, Transaction, TransactionSource
from app.services.budgets import BudgetService

UID = "u1"


def _add(repo, tid, cents, category, *, transfer=False, d=date(2026, 6, 10)):
    repo.upsert_transaction(
        UID,
        Transaction(
            id=tid,
            account_id="a1",
            amount_cents=cents,
            date=d,
            merchant=tid,
            category=category,
            is_transfer=transfer,
            source=TransactionSource.PLAID,
        ),
    )


def test_recompute_sums_spend_by_category_excluding_transfers_and_income():
    repo = MemoryRepository()
    _add(repo, "t1", -2000, Category.GROCERIES)
    _add(repo, "t2", -1000, Category.GROCERIES)
    _add(repo, "t3", -5000, Category.TRANSPORT)
    _add(repo, "t4", 300000, Category.INCOME)  # income excluded
    _add(repo, "t5", -9999, Category.TRANSFER, transfer=True)  # transfer excluded
    _add(repo, "t6", -1500, Category.GROCERIES, d=date(2026, 5, 9))  # different month

    budget = BudgetService(repo).recompute_month(UID, "2026-06")

    assert budget.spent_cents["GROCERIES"] == 3000
    assert budget.spent_cents["TRANSPORT"] == 5000
    assert "INCOME" not in budget.spent_cents
    assert "TRANSFER" not in budget.spent_cents


def test_recompute_preserves_existing_caps():
    repo = MemoryRepository()
    repo.upsert_budget(UID, Budget(month="2026-06", caps_cents={"GROCERIES": 40000}))
    _add(repo, "t1", -2500, Category.GROCERIES)

    budget = BudgetService(repo).recompute_month(UID, "2026-06")

    assert budget.caps_cents == {"GROCERIES": 40000}
    assert budget.spent_cents["GROCERIES"] == 2500
