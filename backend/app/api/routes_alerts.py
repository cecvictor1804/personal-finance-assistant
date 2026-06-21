"""Alert endpoints: list (optionally unread-only) and mark read."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_uid, get_repository
from app.api.schemas import MessageOut
from app.domain.models import Alert
from app.ports.repository import Repository

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[Alert])
def list_alerts(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
    limit: int = Query(default=50, le=200),
    unread_only: bool = False,
):
    return repo.list_alerts(uid, limit=limit, unread_only=unread_only)


@router.post("/{alert_id}/read", response_model=MessageOut)
def mark_read(
    alert_id: str,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    repo.mark_alert_read(uid, alert_id)
    return MessageOut(message="ok")
