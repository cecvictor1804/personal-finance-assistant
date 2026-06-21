"""Cash-flow forecast: project the next N days of recurring inflows/outflows against liquid balances.

A simple, explainable projection built from active recurring streams: step each stream forward from
its last occurrence by its frequency and collect occurrences landing inside the horizon. The end
balance is today's liquid (depository) balance plus net projected flow.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.domain.models import CashFlowForecast, Flow, RecurringStream, UpcomingCashFlow
from app.ports.repository import Repository

# Approximate days between occurrences per Plaid frequency.
FREQUENCY_DAYS: dict[str, int] = {
    "WEEKLY": 7,
    "BIWEEKLY": 14,
    "SEMI_MONTHLY": 15,
    "MONTHLY": 30,
    "ANNUALLY": 365,
    "UNKNOWN": 30,
}

_MAX_STEPS = 1000  # safety bound for very old last_dates


def _next_occurrences(stream: RecurringStream, today: date, horizon_days: int) -> list[date]:
    if stream.last_date is None:
        return []
    interval = FREQUENCY_DAYS.get(stream.frequency.upper(), 30)
    end = today + timedelta(days=horizon_days)
    occurrences: list[date] = []
    d = stream.last_date
    steps = 0
    while d <= today and steps < _MAX_STEPS:
        d += timedelta(days=interval)
        steps += 1
    while d <= end and steps < _MAX_STEPS:
        occurrences.append(d)
        d += timedelta(days=interval)
        steps += 1
    return occurrences


class CashFlowService:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def forecast(self, uid: str, *, horizon_days: int, today: date) -> CashFlowForecast:
        upcoming: list[UpcomingCashFlow] = []
        for stream in self._repo.get_recurring_streams(uid):
            if not stream.is_active:
                continue
            for occ in _next_occurrences(stream, today, horizon_days):
                upcoming.append(
                    UpcomingCashFlow(
                        date=occ,
                        merchant=stream.merchant,
                        amount_cents=stream.average_amount_cents,
                        flow=stream.flow,
                        category=stream.category,
                    )
                )
        upcoming.sort(key=lambda u: u.date)

        inflow = sum(u.amount_cents for u in upcoming if u.flow == Flow.INFLOW)
        outflow = sum(u.amount_cents for u in upcoming if u.flow == Flow.OUTFLOW)  # negative
        current = sum(
            a.balance_cents
            for a in self._repo.get_accounts(uid)
            if a.type == "depository" and not a.is_liability
        )
        net = inflow + outflow
        return CashFlowForecast(
            horizon_days=horizon_days,
            current_balance_cents=current,
            projected_inflow_cents=inflow,
            projected_outflow_cents=outflow,
            net_cents=net,
            projected_end_balance_cents=current + net,
            upcoming=upcoming,
        )
