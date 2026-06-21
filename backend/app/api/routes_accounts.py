"""Account endpoints: list balances (used by the dashboard's net-worth and balances views)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_uid, get_repository
from app.domain.models import Account
from app.ports.repository import Repository

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[Account])
def list_accounts(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    return repo.get_accounts(uid)
