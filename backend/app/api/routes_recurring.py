"""Recurring-stream and cash-flow-forecast endpoints."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_current_uid,
    get_forecast_service,
    get_recurring_service,
    get_repository,
)
from app.api.schemas import SyncResultOut
from app.domain.models import CashFlowForecast, RecurringStream
from app.ports.repository import Repository
from app.services.forecast import CashFlowService
from app.services.recurring import RecurringService

router = APIRouter(tags=["recurring"])


@router.get("/recurring", response_model=list[RecurringStream])
def list_recurring(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    streams = repo.get_recurring_streams(uid)
    # Active first, then by absolute average amount (biggest commitments on top).
    streams.sort(key=lambda s: (not s.is_active, -abs(s.average_amount_cents)))
    return streams


@router.post("/recurring/refresh", response_model=SyncResultOut)
def refresh_recurring(
    uid: str = Depends(get_current_uid),
    recurring: RecurringService = Depends(get_recurring_service),
):
    created = recurring.refresh_all(uid)
    return SyncResultOut(added=0, modified=0, removed=0, flagged_duplicates=len(created))


@router.get("/forecast", response_model=CashFlowForecast)
def get_forecast(
    uid: str = Depends(get_current_uid),
    forecast: CashFlowService = Depends(get_forecast_service),
    horizon_days: int = Query(default=30, ge=1, le=365),
):
    return forecast.forecast(uid, horizon_days=horizon_days, today=date.today())
