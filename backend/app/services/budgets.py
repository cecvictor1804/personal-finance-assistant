"""Budget recompute: roll a month's transactions into per-category spend.

Spend excludes transfers and income (consistent with the dashboard selectors), so moving money
between your own accounts never counts against a budget.
"""

from __future__ import annotations

from app.domain.categories import Category
from app.domain.models import Budget, Transaction
from app.ports.repository import Repository


def is_spend(t: Transaction) -> bool:
    return t.amount_cents < 0 and not t.is_transfer and t.category != Category.INCOME


def month_of(date_iso: str) -> str:
    return date_iso[:7]


class BudgetService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def recompute_month(self, uid: str, month: str) -> Budget:
        """Recompute spent-per-category for `month`, preserving any user-set caps."""
        spent: dict[str, int] = {}
        for t in self._repo.get_transactions_for_month(uid, month):
            if not is_spend(t):
                continue
            key = t.category.value
            spent[key] = spent.get(key, 0) + abs(t.amount_cents)

        existing = self._repo.get_budget(uid, month)
        budget = Budget(
            month=month,
            caps_cents=existing.caps_cents if existing else {},
            spent_cents=spent,
        )
        self._repo.upsert_budget(uid, budget)
        return budget
