"""Money is represented everywhere as signed integer minor units (cents).

Sign convention (internal): **negative = money leaving the account (spending/outflow);
positive = money entering (income/inflow).** This is the inverse of Plaid's raw `amount`
(positive = outflow), so :func:`from_plaid_amount` flips the sign at ingestion.

Floats never touch persistence. Conversions use :class:`decimal.Decimal` to avoid binary
floating-point rounding error (e.g. 0.1 + 0.2).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def to_cents(amount: float | int | str | Decimal) -> int:
    """Convert a major-unit amount (e.g. dollars) to integer cents, half-up rounded."""
    quantized = (Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(quantized)


def from_cents(cents: int) -> Decimal:
    """Convert integer cents back to a major-unit Decimal (for display/serialization)."""
    return (Decimal(cents) / 100).quantize(Decimal("0.01"))


def from_plaid_amount(plaid_amount: float | int | str | Decimal) -> int:
    """Normalize a Plaid `amount` to internal signed cents.

    Plaid: positive => money out of the account (a purchase). Internal: negative => outflow.
    """
    return -to_cents(plaid_amount)


def format_cents(cents: int, currency: str = "USD") -> str:
    """Human-readable money string, e.g. -1234 -> '-$12.34'. Display only."""
    symbol = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "$"}.get(currency, "")
    value = from_cents(abs(cents))
    sign = "-" if cents < 0 else ""
    return f"{sign}{symbol}{value}"


def is_outflow(cents: int) -> bool:
    return cents < 0


def is_inflow(cents: int) -> bool:
    return cents > 0
