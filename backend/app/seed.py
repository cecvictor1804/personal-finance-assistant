"""Demo data seeding for local development.

Populates the in-memory repository with a realistic personal-finance dataset — four accounts,
~40 transactions across the current and prior two months (salary income + varied spending, plus a
pending charge and a flagged duplicate), current-month budget caps, and a couple of categorization
rules — so the app has something to show when run with ``APP_ENV=local`` + ``AUTH_DISABLED=true``.

Enabled via ``SEED_DEMO_DATA=true`` and invoked from :mod:`app.main`'s lifespan. Idempotent: every
record uses a fixed id, so re-running on each startup overwrites rather than duplicates. Dates are
computed relative to ``date.today()`` so the data always lands in the current and prior two months.
"""

from __future__ import annotations

import calendar
from datetime import date

from app.domain.categories import Category
from app.domain.models import (
    Account,
    Budget,
    CategorySource,
    MatchType,
    Rule,
    Transaction,
    TransactionSource,
)
from app.domain.money import to_cents
from app.ports.repository import Repository

CHECKING = "seed-acc-checking"
SAVINGS = "seed-acc-savings"
CARD = "seed-acc-card"
INVEST = "seed-acc-invest"


def _month_start(today: date, months_back: int) -> date:
    """First day of the month ``months_back`` months before ``today``."""
    index = today.year * 12 + (today.month - 1) - months_back
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


def _in_month(month_start: date, day: int, *, not_after: date | None = None) -> date:
    """A date on ``day`` within ``month_start``'s month, clamped to the month length and,
    for the current month, to ``not_after`` so we never seed future-dated rows."""
    last_day = calendar.monthrange(month_start.year, month_start.month)[1]
    when = month_start.replace(day=min(day, last_day))
    if not_after is not None and when > not_after:
        return not_after
    return when


def _accounts() -> list[Account]:
    return [
        Account(
            id=CHECKING, name="Everyday Checking", type="depository", subtype="checking",
            mask="1234", balance_cents=to_cents("4248.55"),
        ),
        Account(
            id=SAVINGS, name="High-Yield Savings", type="depository", subtype="savings",
            mask="5678", balance_cents=to_cents("15000.00"),
        ),
        Account(
            id=CARD, name="Sapphire Credit Card", type="credit", subtype="credit card",
            mask="9012", balance_cents=to_cents("1847.32"), is_asset=False, is_liability=True,
        ),
        Account(
            id=INVEST, name="Brokerage", type="investment", subtype="brokerage",
            mask="3456", balance_cents=to_cents("32150.00"),
        ),
    ]


# (day, account, merchant, category, dollars) — repeated every month. Income is flagged separately.
_MONTHLY_SPEND: list[tuple[int, str, str, Category, str]] = [
    (1, CHECKING, "Sunset Apartments", Category.RENT_MORTGAGE, "1950.00"),
    (5, CARD, "Netflix", Category.ENTERTAINMENT, "15.99"),
    (7, CARD, "Spotify", Category.ENTERTAINMENT, "10.99"),
    (12, CHECKING, "City Power & Light", Category.BILLS_UTILITIES, "89.99"),
    (18, CARD, "Verizon Wireless", Category.BILLS_UTILITIES, "65.00"),
    (4, CHECKING, "Trader Joe's", Category.GROCERIES, "78.40"),
    (15, CARD, "Whole Foods Market", Category.GROCERIES, "112.30"),
    (8, CARD, "Chipotle", Category.FOOD_DINING, "14.25"),
    (10, CARD, "Starbucks", Category.FOOD_DINING, "6.75"),
    (20, CHECKING, "Local Bistro", Category.FOOD_DINING, "52.80"),
    (9, CARD, "Uber", Category.TRANSPORT, "23.60"),
    (16, CARD, "Shell", Category.TRANSPORT, "41.20"),
    (11, CARD, "Amazon", Category.SHOPPING, "86.99"),
    (22, CARD, "Target", Category.SHOPPING, "54.30"),
]


def _transactions(today: date) -> list[Transaction]:
    txns: list[Transaction] = []
    seq = 0

    def add(
        when: date, account_id: str, merchant: str, category: Category, dollars: str,
        *, income: bool = False, pending: bool = False, duplicate_of: str | None = None,
    ) -> str:
        nonlocal seq
        seq += 1
        tid = f"seed-txn-{seq:04d}"
        cents = to_cents(dollars)
        txns.append(
            Transaction(
                id=tid,
                account_id=account_id,
                amount_cents=cents if income else -cents,
                date=when,
                merchant=merchant,
                raw_name=merchant.upper(),
                category=category,
                category_source=CategorySource.PFC,
                source=TransactionSource.PLAID,
                pending=pending,
                possible_duplicate_of=duplicate_of,
            )
        )
        return tid

    # Oldest month first so generated ids run chronologically.
    for months_back in (2, 1, 0):
        start = _month_start(today, months_back)
        cap = today if months_back == 0 else None

        add(_in_month(start, 1, not_after=cap), CHECKING, "Acme Corp Payroll",
            Category.INCOME, "5200.00", income=True)
        for day, account_id, merchant, category, dollars in _MONTHLY_SPEND:
            add(_in_month(start, day, not_after=cap), account_id, merchant, category, dollars)

        # Current-month extras: a pending charge and a flagged duplicate pair, to exercise badges.
        if months_back == 0:
            recent = _in_month(start, max(1, today.day - 1), not_after=today)
            add(today, CARD, "Amazon Marketplace", Category.SHOPPING, "64.20", pending=True)
            first = add(recent, CARD, "Blue Bottle Coffee", Category.FOOD_DINING, "5.50")
            add(recent, CARD, "Blue Bottle Coffee", Category.FOOD_DINING, "5.50",
                duplicate_of=first)

    return txns


def _budget(today: date) -> Budget:
    """Current-month caps sized against the seeded spend to show a mix of statuses
    (groceries/shopping near limit, dining over, the rest on track)."""
    return Budget(
        month=today.strftime("%Y-%m"),
        caps_cents={
            Category.GROCERIES.value: to_cents(200),
            Category.FOOD_DINING.value: to_cents(70),
            Category.TRANSPORT.value: to_cents(100),
            Category.SHOPPING.value: to_cents(150),
            Category.ENTERTAINMENT.value: to_cents(50),
            Category.BILLS_UTILITIES.value: to_cents(200),
        },
    )


def _rules() -> list[Rule]:
    return [
        Rule(id="seed-rule-coffee", match_type=MatchType.CONTAINS, pattern="starbucks",
             category=Category.FOOD_DINING, priority=50),
        Rule(id="seed-rule-uber", match_type=MatchType.CONTAINS, pattern="uber",
             category=Category.TRANSPORT, priority=50),
    ]


def seed_demo_data(repo: Repository, uid: str) -> None:
    """Idempotently populate ``repo`` with the demo dataset for ``uid``."""
    today = date.today()
    for account in _accounts():
        repo.upsert_account(uid, account)
    for txn in _transactions(today):
        repo.upsert_transaction(uid, txn)
    repo.upsert_budget(uid, _budget(today))
    for rule in _rules():
        repo.add_rule(uid, rule)
