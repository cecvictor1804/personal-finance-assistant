"""Translate provider-shaped (Plaid) dicts into domain models.

This is the single seam between the provider's wire format and the rest of the system. Category
assignment is deliberately *not* done here — the sync orchestrator runs the categorization service
after normalization so the same logic applies to manual entries too.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.domain.categories import TRANSFER_CATEGORIES, map_pfc
from app.domain.models import Account, Flow, RecurringStream, Transaction, TransactionSource
from app.domain.money import from_plaid_amount, to_cents

# Plaid account types that represent debt rather than assets.
_LIABILITY_TYPES = {"credit", "loan"}


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise ValueError(f"Unparseable transaction date: {value!r}")


def _pfc(raw: dict[str, Any]) -> tuple[str | None, str | None]:
    pfc = raw.get("personal_finance_category") or {}
    return pfc.get("primary"), pfc.get("detailed")


def normalize_transaction(raw: dict[str, Any]) -> Transaction:
    """Map a Plaid transaction dict to a domain Transaction (category left to categorization)."""
    primary, detailed = _pfc(raw)
    merchant = (raw.get("merchant_name") or raw.get("name") or "").strip()
    mapped = map_pfc(primary, detailed)
    return Transaction(
        id=f"plaid_{raw['transaction_id']}",
        account_id=raw["account_id"],
        amount_cents=from_plaid_amount(raw["amount"]),
        currency=raw.get("iso_currency_code") or "USD",
        date=_to_date(raw["date"]),
        merchant=merchant,
        raw_name=(raw.get("name") or "").strip(),
        pfc_primary=primary,
        pfc_detailed=detailed,
        source=TransactionSource.PLAID,
        pending=bool(raw.get("pending", False)),
        country=transaction_country(raw),
        plaid_txn_id=raw["transaction_id"],
        is_transfer=mapped in TRANSFER_CATEGORIES,
    )


def transaction_country(raw: dict[str, Any]) -> str | None:
    """Best-effort country code for a raw Plaid txn (used by the foreign-charge alert rule)."""
    return (raw.get("location") or {}).get("country")


def normalize_recurring(raw: dict[str, Any]) -> RecurringStream:
    """Map a Plaid recurring stream to a domain RecurringStream.

    The Plaid adapter tags each stream with ``flow`` (which inflow/outflow list it came from).
    Amounts are normalized to signed cents: outflow negative, inflow positive.
    """
    flow = Flow(raw.get("flow", "outflow"))
    sign = 1 if flow == Flow.INFLOW else -1
    avg = abs(to_cents((raw.get("average_amount") or {}).get("amount") or 0))
    last = abs(to_cents((raw.get("last_amount") or {}).get("amount") or 0))
    primary, detailed = _pfc(raw)
    return RecurringStream(
        id=raw["stream_id"],
        merchant=(raw.get("merchant_name") or raw.get("description") or "").strip(),
        description=(raw.get("description") or "").strip(),
        category=map_pfc(primary, detailed),
        frequency=(raw.get("frequency") or "UNKNOWN"),
        flow=flow,
        average_amount_cents=sign * avg,
        last_amount_cents=sign * last,
        last_date=_to_date(raw["last_date"]) if raw.get("last_date") else None,
        is_active=bool(raw.get("is_active", True)),
        status=raw.get("status") or "",
    )


def normalize_account(raw: dict[str, Any]) -> Account:
    """Map a Plaid account dict to a domain Account. Balances are stored as positive cents."""
    acct_type = (raw.get("type") or "").lower()
    is_liability = acct_type in _LIABILITY_TYPES
    balances = raw.get("balances") or {}
    current = balances.get("current") or 0
    return Account(
        id=raw["account_id"],
        plaid_account_id=raw["account_id"],
        name=(raw.get("name") or "").strip(),
        mask=raw.get("mask"),
        type=acct_type,
        subtype=raw.get("subtype"),
        balance_cents=to_cents(current),
        currency=balances.get("iso_currency_code") or "USD",
        is_asset=not is_liability,
        is_liability=is_liability,
    )
