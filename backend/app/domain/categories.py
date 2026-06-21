"""Internal category taxonomy and the Plaid Personal Finance Category (PFC) -> internal mapping.

Categorization precedence (see services/categorization.py): user rule -> PFC mapping -> UNCATEGORIZED.
Keeping the taxonomy small and stable makes budgets and trend rollups intuitive; Plaid's richer
PFC is collapsed into it here.
"""

from __future__ import annotations

from enum import Enum


class Category(str, Enum):
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"  # movement between the user's own accounts; excluded from spend
    FOOD_DINING = "FOOD_DINING"
    GROCERIES = "GROCERIES"
    SHOPPING = "SHOPPING"
    TRANSPORT = "TRANSPORT"
    TRAVEL = "TRAVEL"
    BILLS_UTILITIES = "BILLS_UTILITIES"
    RENT_MORTGAGE = "RENT_MORTGAGE"
    HEALTHCARE = "HEALTHCARE"
    ENTERTAINMENT = "ENTERTAINMENT"
    PERSONAL_CARE = "PERSONAL_CARE"
    EDUCATION = "EDUCATION"
    FEES_CHARGES = "FEES_CHARGES"
    LOAN_PAYMENT = "LOAN_PAYMENT"
    TAXES_GOV = "TAXES_GOV"
    GIFTS_DONATIONS = "GIFTS_DONATIONS"
    BUSINESS_SERVICES = "BUSINESS_SERVICES"
    UNCATEGORIZED = "UNCATEGORIZED"


# Categories that represent moving money between the user's own accounts. These are excluded
# from spending totals / budgets so transfers don't double-count.
TRANSFER_CATEGORIES = frozenset({Category.TRANSFER})

# Plaid PFC *primary* -> internal category.
_PFC_PRIMARY: dict[str, Category] = {
    "INCOME": Category.INCOME,
    "TRANSFER_IN": Category.TRANSFER,
    "TRANSFER_OUT": Category.TRANSFER,
    "LOAN_PAYMENTS": Category.LOAN_PAYMENT,
    "BANK_FEES": Category.FEES_CHARGES,
    "ENTERTAINMENT": Category.ENTERTAINMENT,
    "FOOD_AND_DRINK": Category.FOOD_DINING,
    "GENERAL_MERCHANDISE": Category.SHOPPING,
    "HOME_IMPROVEMENT": Category.SHOPPING,
    "MEDICAL": Category.HEALTHCARE,
    "PERSONAL_CARE": Category.PERSONAL_CARE,
    "GENERAL_SERVICES": Category.BUSINESS_SERVICES,
    "GOVERNMENT_AND_NON_PROFIT": Category.TAXES_GOV,
    "TRANSPORTATION": Category.TRANSPORT,
    "TRAVEL": Category.TRAVEL,
    "RENT_AND_UTILITIES": Category.BILLS_UTILITIES,
}

# Plaid PFC *detailed* overrides where the primary mapping is too coarse.
_PFC_DETAILED: dict[str, Category] = {
    "FOOD_AND_DRINK_GROCERIES": Category.GROCERIES,
    "RENT_AND_UTILITIES_RENT": Category.RENT_MORTGAGE,
    "LOAN_PAYMENTS_MORTGAGE_PAYMENT": Category.RENT_MORTGAGE,
    "GENERAL_SERVICES_EDUCATION": Category.EDUCATION,
    "GOVERNMENT_AND_NON_PROFIT_DONATIONS": Category.GIFTS_DONATIONS,
    "GENERAL_MERCHANDISE_GIFTS_AND_DONATIONS": Category.GIFTS_DONATIONS,
}


def map_pfc(primary: str | None, detailed: str | None = None) -> Category:
    """Map a Plaid PFC (primary + optional detailed) to an internal category.

    Detailed overrides win when present; otherwise fall back to the primary mapping, then
    UNCATEGORIZED. Inputs are case-insensitive and tolerate None.
    """
    if detailed:
        hit = _PFC_DETAILED.get(detailed.strip().upper())
        if hit is not None:
            return hit
    if primary:
        hit = _PFC_PRIMARY.get(primary.strip().upper())
        if hit is not None:
            return hit
    return Category.UNCATEGORIZED


def is_valid_category(value: str) -> bool:
    return value in Category._value2member_map_
