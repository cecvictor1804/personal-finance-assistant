from datetime import date

from app.adapters.memory_repo import MemoryRepository
from app.domain.models import Account, Flow, RecurringStream
from app.services.forecast import CashFlowService

UID = "u1"


def _stream(sid, cents, flow, freq, last, active=True):
    return RecurringStream(
        id=sid,
        merchant=sid,
        flow=flow,
        average_amount_cents=cents,
        frequency=freq,
        last_date=last,
        is_active=active,
    )


def test_forecast_projects_inflow_outflow_and_end_balance():
    repo = MemoryRepository()
    repo.upsert_account(UID, Account(id="a1", name="Checking", type="depository",
                                     balance_cents=100000))
    repo.upsert_recurring(UID, _stream("rent", -150000, Flow.OUTFLOW, "MONTHLY", date(2026, 5, 1)))
    repo.upsert_recurring(UID, _stream("pay", 300000, Flow.INFLOW, "MONTHLY", date(2026, 5, 5)))

    fc = CashFlowService(repo).forecast(UID, horizon_days=30, today=date(2026, 5, 20))

    assert fc.projected_outflow_cents == -150000
    assert fc.projected_inflow_cents == 300000
    assert fc.net_cents == 150000
    assert fc.current_balance_cents == 100000
    assert fc.projected_end_balance_cents == 250000
    assert len(fc.upcoming) == 2


def test_forecast_weekly_multiple_occurrences():
    repo = MemoryRepository()
    repo.upsert_recurring(UID, _stream("coffee", -1000, Flow.OUTFLOW, "WEEKLY", date(2026, 5, 19)))

    fc = CashFlowService(repo).forecast(UID, horizon_days=30, today=date(2026, 5, 20))

    # 5/26, 6/2, 6/9, 6/16 within [5/20, 6/19]
    assert len(fc.upcoming) == 4
    assert fc.projected_outflow_cents == -4000


def test_forecast_excludes_inactive_streams():
    repo = MemoryRepository()
    repo.upsert_recurring(UID, _stream("old", -5000, Flow.OUTFLOW, "MONTHLY", date(2026, 5, 1),
                                       active=False))

    fc = CashFlowService(repo).forecast(UID, horizon_days=60, today=date(2026, 5, 20))

    assert fc.upcoming == []
    assert fc.projected_outflow_cents == 0
