"""Transaction endpoints: list, manual entry, recategorize, fetch one."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_uid, get_repository
from app.api.schemas import ManualTransactionIn, RecategorizeIn
from app.domain.categories import TRANSFER_CATEGORIES
from app.domain.models import CategorySource, Transaction, TransactionSource
from app.ports.repository import Repository
from app.services.categorization import apply_categorization, make_override_rule

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[Transaction])
def list_transactions(
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
    limit: int = Query(default=50, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    account_id: str | None = None,
):
    return repo.list_transactions(
        uid,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        category=category,
        account_id=account_id,
    )


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_manual_transaction(
    body: ManualTransactionIn,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    txn = Transaction(
        id=f"manual_{uuid.uuid4().hex[:12]}",
        account_id=body.account_id,
        amount_cents=body.amount_cents,
        date=body.date,
        merchant=body.merchant,
        raw_name=body.merchant,
        notes=body.notes,
        source=TransactionSource.MANUAL,
    )
    if body.category is not None:
        txn.category = body.category
        txn.category_source = CategorySource.MANUAL
        txn.is_transfer = body.category in TRANSFER_CATEGORIES
    else:
        txn = apply_categorization(txn, repo.get_rules(uid))
        txn.is_transfer = txn.category in TRANSFER_CATEGORIES
    repo.upsert_transaction(uid, txn)
    return txn


@router.get("/{txn_id}", response_model=Transaction)
def get_transaction(
    txn_id: str,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    txn = repo.get_transaction(uid, txn_id)
    if txn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return txn


@router.post("/{txn_id}/recategorize", response_model=Transaction)
def recategorize(
    txn_id: str,
    body: RecategorizeIn,
    uid: str = Depends(get_current_uid),
    repo: Repository = Depends(get_repository),
):
    txn = repo.get_transaction(uid, txn_id)
    if txn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")

    txn.category = body.category
    txn.category_source = CategorySource.MANUAL
    txn.is_transfer = body.category in TRANSFER_CATEGORIES
    repo.upsert_transaction(uid, txn)

    # "Remember this for {merchant}" — create an exact-match rule for future transactions.
    if body.remember and txn.merchant:
        repo.add_rule(uid, make_override_rule(txn.merchant, body.category))

    return txn
