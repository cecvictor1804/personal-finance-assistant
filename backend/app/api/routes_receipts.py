"""Receipt endpoints: list parsed receipts, confirm-attach to a transaction, and the internal
Pub/Sub endpoint that runs OCR processing for a newly uploaded receipt.
"""

from __future__ import annotations

import base64
import json

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.api.deps import get_current_uid, get_receipt_service, get_repository, get_settings
from app.api.schemas import AttachReceiptIn
from app.config import Settings
from app.domain.models import Receipt
from app.ports.repository import Repository
from app.services.receipts import ReceiptService

router = APIRouter(prefix="/receipts", tags=["receipts"])
internal_router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("", response_model=list[Receipt])
def list_receipts(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
    limit: int = Query(default=50, le=200),
):
    return repo.list_receipts(uid, limit=limit)


@router.post("/{receipt_id}/attach", response_model=Receipt)
def attach_receipt(
    receipt_id: str,
    body: AttachReceiptIn,
    uid: str = Depends(get_current_uid),
    receipts: ReceiptService = Depends(get_receipt_service),
):
    try:
        return receipts.attach(uid, receipt_id, body.txn_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@internal_router.post("/pubsub/receipt", status_code=status.HTTP_204_NO_CONTENT)
def pubsub_receipt(
    envelope: dict = Body(...),
    token: str = Query(default=""),
    receipts: ReceiptService = Depends(get_receipt_service),
    settings: Settings = Depends(get_settings),
):
    """Pub/Sub push target for the Storage-upload -> OCR pipeline.

    Message payload: {uid, receipt_id, bucket, path}. Always 2xx on a handled/malformed message so
    Pub/Sub doesn't redeliver forever.
    """
    if not settings.internal_secret or token != settings.internal_secret:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")

    message = envelope.get("message") or {}
    data_b64 = message.get("data")
    if not data_b64:
        return
    try:
        data = json.loads(base64.b64decode(data_b64).decode("utf-8"))
        receipts.process(data["uid"], data["receipt_id"], data["bucket"], data["path"])
    except (ValueError, KeyError):
        return
