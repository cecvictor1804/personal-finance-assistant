"""Budget endpoints: read a month's progress (spent recomputed on read) and set category caps."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_alert_engine, get_budget_service, get_current_uid, get_repository
from app.api.schemas import BudgetCapsIn
from app.domain.models import Budget
from app.ports.repository import Repository
from app.services.alerts import AlertEngine
from app.services.budgets import BudgetService

router = APIRouter(prefix="/budgets", tags=["budgets"])

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def _validate_month(month: str) -> None:
    if not _MONTH_RE.match(month):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "month must be YYYY-MM")


@router.get("/{month}", response_model=Budget)
def get_budget(
    month: str,
    uid: str = Depends(get_current_uid),
    budgets: BudgetService = Depends(get_budget_service),
):
    _validate_month(month)
    return budgets.recompute_month(uid, month)


@router.put("/{month}", response_model=Budget)
def set_caps(
    month: str,
    body: BudgetCapsIn,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
    budgets: BudgetService = Depends(get_budget_service),
    alerts: AlertEngine = Depends(get_alert_engine),
):
    _validate_month(month)
    budget = budgets.recompute_month(uid, month)
    budget.caps_cents = body.caps_cents
    repo.upsert_budget(uid, budget)
    # Setting a cap below current spend should surface immediately.
    alerts.evaluate_budget(uid, budget)
    return budget
