"""Precomputed aggregates written to the `rollups` collection.

Net-worth snapshots accumulate daily so a net-worth-over-time chart has history to draw (you can't
backfill a balance you never recorded). Monthly category rollups give the dashboard a cheap read
instead of scanning every transaction.
"""

from __future__ import annotations

from datetime import date

from app.services.budgets import is_spend
from app.ports.repository import Repository


class RollupService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def snapshot_net_worth(self, uid: str, on: date) -> dict:
        accounts = self._repo.get_accounts(uid)
        assets = sum(a.balance_cents for a in accounts if not a.is_liability)
        liabilities = sum(a.balance_cents for a in accounts if a.is_liability)
        doc = {
            "kind": "netWorthSnapshot",
            "period": on.isoformat(),
            "data": {
                "assets_cents": assets,
                "liabilities_cents": liabilities,
                "net_cents": assets - liabilities,
            },
        }
        self._repo.upsert_rollup(uid, f"networth_{on.isoformat()}", doc)
        return doc

    def recompute_month_category(self, uid: str, month: str) -> dict:
        by_category: dict[str, int] = {}
        for t in self._repo.get_transactions_for_month(uid, month):
            if not is_spend(t):
                continue
            by_category[t.category.value] = by_category.get(t.category.value, 0) + abs(t.amount_cents)
        doc = {"kind": "monthlyByCategory", "period": month, "data": by_category}
        self._repo.upsert_rollup(uid, f"monthcat_{month}", doc)
        return doc
