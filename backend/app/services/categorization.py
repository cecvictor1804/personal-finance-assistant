"""Categorization: user rules first, then Plaid PFC mapping, then UNCATEGORIZED.

When the user manually recategorizes a transaction, the API offers to remember it as a rule
(``make_override_rule``) so the same merchant is auto-categorized next time.
"""

from __future__ import annotations

import uuid

from app.domain.categories import Category, map_pfc
from app.domain.models import CategorySource, MatchType, Rule, Transaction

# Priority for auto-generated "remember this" rules: lower number = evaluated before generic rules.
OVERRIDE_RULE_PRIORITY = 10


def categorize(txn: Transaction, rules: list[Rule]) -> tuple[Category, CategorySource]:
    """Resolve a transaction's category. Pure function over the transaction + the user's rules."""
    for rule in sorted(rules, key=lambda r: (r.priority, r.created_at)):
        if rule.matches(txn.merchant) or rule.matches(txn.raw_name):
            return rule.category, CategorySource.RULE

    mapped = map_pfc(txn.pfc_primary, txn.pfc_detailed)
    if mapped is not Category.UNCATEGORIZED:
        return mapped, CategorySource.PFC

    return Category.UNCATEGORIZED, CategorySource.DEFAULT


def apply_categorization(txn: Transaction, rules: list[Rule]) -> Transaction:
    """Return a copy of `txn` with category/category_source filled in."""
    category, source = categorize(txn, rules)
    return txn.model_copy(update={"category": category, "category_source": source})


def make_override_rule(merchant: str, category: Category) -> Rule:
    """Build an exact-match rule remembering a user's manual recategorization of a merchant."""
    return Rule(
        id=f"rule_{uuid.uuid4().hex[:12]}",
        match_type=MatchType.EQUALS,
        pattern=merchant.strip(),
        category=category,
        priority=OVERRIDE_RULE_PRIORITY,
    )
