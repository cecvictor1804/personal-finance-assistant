"""Domain models. Plain pydantic types shared by services, adapters, and the API layer.

These are storage/transport-neutral: repositories translate them to/from Firestore documents,
and the API layer maps them to/from request/response schemas.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from datetime import date as _date  # alias: lets optional fields named `date` reference the type
from enum import Enum

from pydantic import BaseModel, Field

from .categories import Category


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TransactionSource(str, Enum):
    PLAID = "plaid"
    MANUAL = "manual"


class CategorySource(str, Enum):
    RULE = "rule"      # matched a user-defined rule
    PFC = "pfc"        # derived from Plaid's category
    MANUAL = "manual"  # user set it directly on the transaction
    DEFAULT = "default"  # fell through to UNCATEGORIZED


class MatchType(str, Enum):
    CONTAINS = "contains"
    EQUALS = "equals"
    REGEX = "regex"


class ItemStatus(str, Enum):
    ACTIVE = "active"
    NEEDS_REAUTH = "needsReauth"  # Plaid ITEM_LOGIN_REQUIRED
    ERROR = "error"


class AlertType(str, Enum):
    LARGE_TRANSACTION = "large_transaction"
    NEW_MERCHANT = "new_merchant"
    FOREIGN_TRANSACTION = "foreign_transaction"
    RAPID_REPEAT = "rapid_repeat"          # same merchant + amount seen again same day (double charge)
    BUDGET_WARNING = "budget_warning"      # category spend crossed the warn threshold
    BUDGET_EXCEEDED = "budget_exceeded"    # category spend exceeded its cap
    NEW_RECURRING = "new_recurring"        # a new subscription/recurring charge was detected
    RECURRING_AMOUNT_CHANGE = "recurring_amount_change"  # a recurring charge changed amount


class Flow(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class ReceiptStatus(str, Enum):
    PENDING = "pending"   # uploaded, not yet processed
    PARSED = "parsed"     # OCR done, no confident transaction match
    MATCHED = "matched"   # linked to a transaction
    ERROR = "error"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Account(BaseModel):
    id: str
    plaid_account_id: str | None = None
    name: str
    mask: str | None = None
    type: str                 # depository | credit | loan | investment
    subtype: str | None = None
    institution_id: str | None = None
    balance_cents: int = 0
    currency: str = "USD"
    is_asset: bool = True
    is_liability: bool = False
    updated_at: datetime = Field(default_factory=utcnow)


class Transaction(BaseModel):
    id: str
    account_id: str
    amount_cents: int                       # signed: negative = outflow/spending
    currency: str = "USD"
    date: date
    merchant: str = ""
    raw_name: str = ""
    category: Category = Category.UNCATEGORIZED
    category_source: CategorySource = CategorySource.DEFAULT
    pfc_primary: str | None = None
    pfc_detailed: str | None = None
    source: TransactionSource = TransactionSource.PLAID
    pending: bool = False
    country: str | None = None               # ISO country from Plaid location (foreign-charge rule)
    plaid_txn_id: str | None = None
    receipt_id: str | None = None
    possible_duplicate_of: str | None = None  # txn id this is a suspected dup of
    is_transfer: bool = False
    notes: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Rule(BaseModel):
    """User-defined categorization rule. Lower `priority` number = evaluated first."""

    id: str
    match_type: MatchType
    pattern: str
    category: Category
    priority: int = 100
    created_at: datetime = Field(default_factory=utcnow)

    def matches(self, merchant: str) -> bool:
        target = (merchant or "").strip().lower()
        pat = self.pattern.strip().lower()
        if not target or not pat:
            return False
        if self.match_type == MatchType.EQUALS:
            return target == pat
        if self.match_type == MatchType.CONTAINS:
            return pat in target
        if self.match_type == MatchType.REGEX:
            try:
                return re.search(self.pattern, merchant or "", re.IGNORECASE) is not None
            except re.error:
                return False
        return False


class PlaidItem(BaseModel):
    """Per-institution Plaid connection metadata (client-readable subset)."""

    id: str
    institution_id: str | None = None
    institution_name: str = ""
    status: ItemStatus = ItemStatus.ACTIVE
    products: list[str] = Field(default_factory=list)
    last_sync_at: datetime | None = None


class Budget(BaseModel):
    month: str                              # "YYYY-MM"
    caps_cents: dict[str, int] = Field(default_factory=dict)   # category -> cap
    spent_cents: dict[str, int] = Field(default_factory=dict)  # category -> spent (recomputed)
    updated_at: datetime = Field(default_factory=utcnow)


class Alert(BaseModel):
    id: str
    type: AlertType
    severity: Severity = Severity.INFO
    title: str
    message: str
    txn_id: str | None = None
    category: Category | None = None
    amount_cents: int | None = None
    read: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class UserSettings(BaseModel):
    """Per-user alerting configuration. Defaults mirror the backend Settings."""

    large_txn_threshold_cents: int = 50_000   # $500
    budget_warn_percent: int = 80
    home_country: str = "US"
    email: str | None = None                  # where alert emails go
    fcm_tokens: list[str] = Field(default_factory=list)


class RecurringStream(BaseModel):
    """A Plaid recurring transaction stream (subscription / recurring bill or income)."""

    id: str
    merchant: str = ""
    description: str = ""
    category: Category = Category.UNCATEGORIZED
    frequency: str = "UNKNOWN"               # WEEKLY|BIWEEKLY|SEMI_MONTHLY|MONTHLY|ANNUALLY|UNKNOWN
    flow: Flow = Flow.OUTFLOW
    average_amount_cents: int = 0            # signed: negative = outflow
    last_amount_cents: int = 0              # signed
    last_date: date | None = None
    is_active: bool = True
    status: str = ""                         # Plaid stream status (MATURE|EARLY|TOMBSTONED|...)
    updated_at: datetime = Field(default_factory=utcnow)


class UpcomingCashFlow(BaseModel):
    date: date
    merchant: str
    amount_cents: int                        # signed
    flow: Flow
    category: Category = Category.UNCATEGORIZED


class CashFlowForecast(BaseModel):
    horizon_days: int
    current_balance_cents: int               # liquid (depository) balances today
    projected_inflow_cents: int
    projected_outflow_cents: int             # signed (negative)
    net_cents: int
    projected_end_balance_cents: int
    upcoming: list[UpcomingCashFlow] = Field(default_factory=list)


class LineItem(BaseModel):
    description: str = ""
    amount_cents: int = 0                     # positive magnitude


class OcrResult(BaseModel):
    """Parsed output of the receipt OCR (Document AI Expense parser). Pure value object."""

    merchant: str = ""
    total_cents: int = 0                      # positive magnitude
    date: _date | None = None
    currency: str = "USD"
    line_items: list[LineItem] = Field(default_factory=list)
    raw_text: str = ""


class Receipt(BaseModel):
    id: str
    storage_path: str
    status: ReceiptStatus = ReceiptStatus.PENDING
    merchant: str = ""
    total_cents: int = 0
    date: _date | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    matched_txn_id: str | None = None         # suggested or confirmed transaction link
    created_at: datetime = Field(default_factory=utcnow)
