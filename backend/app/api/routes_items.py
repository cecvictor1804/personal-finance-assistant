"""Plaid item endpoints: connection status, manual sync, guided re-link, and the internal
sync endpoint invoked by the webhook -> Pub/Sub pipeline.
"""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.api.deps import (
    get_current_uid,
    get_provider,
    get_repository,
    get_sync_service,
    require_internal_secret,
)
from app.api.schemas import InternalSyncIn, LinkTokenOut, SyncResultOut
from app.config import Settings, get_settings
from app.domain.models import PlaidItem
from app.ports.bank_provider import BankProvider
from app.ports.repository import Repository
from app.services.sync import SyncService

router = APIRouter(prefix="/items", tags=["items"])
internal_router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("", response_model=list[PlaidItem])
def list_items(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    return repo.get_items(uid)


@router.post("/sync", response_model=SyncResultOut)
def sync_now(
    uid: str = Depends(get_current_uid),
    sync: SyncService = Depends(get_sync_service),
):
    """User-triggered refresh of all the user's items (also used by the daily reconcile job)."""
    reports = sync.sync_all_items(uid)
    return SyncResultOut(
        added=sum(r.added for r in reports.values()),
        modified=sum(r.modified for r in reports.values()),
        removed=sum(r.removed for r in reports.values()),
        flagged_duplicates=sum(r.flagged_duplicates for r in reports.values()),
    )


@router.post("/{item_id}/reauth-link-token", response_model=LinkTokenOut)
def reauth_link_token(
    item_id: str,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
    provider: BankProvider = Depends(get_provider),
):
    """Create an update-mode Link token so the user can re-authenticate a broken connection."""
    secret = repo.get_item_secret(item_id)
    if secret is None or secret.uid != uid:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return LinkTokenOut(link_token=provider.create_update_link_token(uid, secret.access_token))


@internal_router.post(
    "/sync", response_model=SyncResultOut, dependencies=[Depends(require_internal_secret)]
)
def internal_sync(
    body: InternalSyncIn,
    sync: SyncService = Depends(get_sync_service),
):
    """Direct internal sync of one item (shared-secret guarded)."""
    report = sync.sync_item(body.uid, body.item_id)
    return SyncResultOut(
        added=report.added,
        modified=report.modified,
        removed=report.removed,
        flagged_duplicates=report.flagged_duplicates,
    )


@internal_router.post("/pubsub/sync", status_code=status.HTTP_204_NO_CONTENT)
def pubsub_sync(
    envelope: dict = Body(...),
    token: str = Query(default=""),
    sync: SyncService = Depends(get_sync_service),
    settings: Settings = Depends(get_settings),
):
    """Pub/Sub push endpoint for the webhook -> Pub/Sub -> sync pipeline.

    The push subscription should be configured with OIDC auth; we additionally check a shared-secret
    `?token=` so the endpoint is safe even if exposed. Always returns 2xx on a handled message so
    Pub/Sub does not redeliver a malformed payload forever.
    """
    if not settings.internal_secret or token != settings.internal_secret:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")

    message = envelope.get("message") or {}
    data_b64 = message.get("data")
    if not data_b64:
        return  # nothing to do; ack
    try:
        data = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        uid, item_id = data["uid"], data["item_id"]
    except (ValueError, KeyError):
        return  # malformed; ack to avoid infinite redelivery
    sync.sync_item(uid, item_id)
