"""Statistical anomaly detection (Phase 7).

Layers on top of the rule-based alert engine: learns each category's *normal* spend from history
and flags a transaction that is a statistical outlier — catching an unusually large charge for a
category even when it's under the fixed "large transaction" threshold.

Uses robust statistics (median + Tukey's IQR fence) rather than mean/standard-deviation, so a few
past outliers don't distort the baseline. Guards against noise with a minimum sample size (cold
start), an absolute floor, and by excluding the transaction being scored from its own baseline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.domain.categories import Category
from app.domain.models import Alert, AlertType, Severity, Transaction, UserSettings
from app.domain.money import format_cents
from app.ports.repository import Repository
from app.services.alerts import AlertEngine
from app.services.budgets import is_spend

MIN_SAMPLES = 8          # need enough history before scoring a category
IQR_K = 3.0              # Tukey "far out" fence — high precision, low noise
ABS_FLOOR_CENTS = 5_000  # ignore trivial amounts ($50) however unusual proportionally
HISTORY_LIMIT = 2000     # trailing transactions used to build baselines


@dataclass
class CategoryBaseline:
    count: int
    median: float
    q1: float
    q3: float
    iqr: float


def _percentile(sorted_values: list[int], p: float) -> float:
    """Linear-interpolation percentile (p in [0, 100]) over a pre-sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (p / 100.0) * (len(sorted_values) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return float(sorted_values[lo])
    frac = rank - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def build_baselines(transactions: list[Transaction]) -> dict[Category, CategoryBaseline]:
    """Build a per-category spend baseline (magnitudes in cents) from history."""
    by_category: dict[Category, list[int]] = {}
    for t in transactions:
        if not is_spend(t):
            continue
        by_category.setdefault(t.category, []).append(abs(t.amount_cents))

    baselines: dict[Category, CategoryBaseline] = {}
    for category, values in by_category.items():
        values.sort()
        q1 = _percentile(values, 25)
        q3 = _percentile(values, 75)
        baselines[category] = CategoryBaseline(
            count=len(values),
            median=_percentile(values, 50),
            q1=q1,
            q3=q3,
            iqr=q3 - q1,
        )
    return baselines


def is_outlier(amount_cents: int, baseline: CategoryBaseline) -> bool:
    """True if a spend (signed cents) is a high outlier vs its category baseline."""
    amount = abs(amount_cents)
    if baseline.count < MIN_SAMPLES or amount < ABS_FLOOR_CENTS:
        return False
    return amount > baseline.q3 + IQR_K * baseline.iqr


def _category_label(category: Category) -> str:
    return category.value.replace("_", " ").title()


class AnomalyDetector:
    def __init__(self, repo: Repository, alert_engine: AlertEngine) -> None:
        self._repo = repo
        self._alert_engine = alert_engine

    def evaluate(self, uid: str, new_txns: list[Transaction]) -> list[Alert]:
        """Score newly added transactions against baselines built from prior history."""
        settings = self._repo.get_settings(uid) or UserSettings()
        if not settings.anomaly_detection_enabled or not new_txns:
            return []

        new_ids = {t.id for t in new_txns}
        history = [
            t
            for t in self._repo.list_transactions(uid, limit=HISTORY_LIMIT)
            if t.id not in new_ids  # exclude the transactions being scored from their own baseline
        ]
        baselines = build_baselines(history)

        created: list[Alert] = []
        for txn in new_txns:
            if not is_spend(txn):
                continue
            baseline = baselines.get(txn.category)
            if baseline is None or not is_outlier(txn.amount_cents, baseline):
                continue
            alert = Alert(
                id=f"anomaly_{txn.id}",
                type=AlertType.ANOMALOUS_SPEND,
                severity=Severity.WARNING,
                title="Unusual spending",
                message=(
                    f"{format_cents(abs(txn.amount_cents))} at "
                    f"{txn.merchant or 'unknown merchant'} is unusually high for "
                    f"{_category_label(txn.category)} (typical ~{format_cents(round(baseline.median))})."
                ),
                txn_id=txn.id,
                category=txn.category,
                amount_cents=txn.amount_cents,
            )
            if self._alert_engine.emit(uid, alert):
                created.append(alert)
        return created
