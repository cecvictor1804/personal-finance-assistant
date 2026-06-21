"""Request/response schemas for the REST API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.domain.categories import Category
from app.domain.models import MatchType


class ManualTransactionIn(BaseModel):
    account_id: str
    amount_cents: int = Field(description="Signed cents; negative = spending/outflow")
    date: date
    merchant: str = ""
    category: Category | None = None
    notes: str = ""


class RecategorizeIn(BaseModel):
    category: Category
    remember: bool = Field(
        default=True, description="Also create an exact-match rule for this merchant"
    )


class RuleIn(BaseModel):
    match_type: MatchType
    pattern: str
    category: Category
    priority: int = 100


class LinkTokenOut(BaseModel):
    link_token: str


class SyncResultOut(BaseModel):
    added: int
    modified: int
    removed: int
    flagged_duplicates: int


class InternalSyncIn(BaseModel):
    uid: str
    item_id: str


class MessageOut(BaseModel):
    message: str


class BudgetCapsIn(BaseModel):
    caps_cents: dict[str, int] = Field(
        description="Category value -> monthly cap in cents", default_factory=dict
    )


class FcmTokenIn(BaseModel):
    token: str
