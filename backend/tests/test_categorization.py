from datetime import date

from app.domain.categories import Category, map_pfc
from app.domain.models import CategorySource, MatchType, Rule, Transaction, TransactionSource
from app.services.categorization import apply_categorization, categorize, make_override_rule


def _txn(merchant="", raw="", pfc_primary=None, pfc_detailed=None) -> Transaction:
    return Transaction(
        id="t1",
        account_id="a1",
        amount_cents=-1000,
        date=date(2026, 1, 1),
        merchant=merchant,
        raw_name=raw,
        pfc_primary=pfc_primary,
        pfc_detailed=pfc_detailed,
        source=TransactionSource.PLAID,
    )


def test_map_pfc_primary_and_detailed():
    assert map_pfc("FOOD_AND_DRINK", None) == Category.FOOD_DINING
    assert map_pfc("FOOD_AND_DRINK", "FOOD_AND_DRINK_GROCERIES") == Category.GROCERIES
    assert map_pfc("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_RENT") == Category.RENT_MORTGAGE
    assert map_pfc("UNKNOWN_THING", None) == Category.UNCATEGORIZED
    assert map_pfc(None, None) == Category.UNCATEGORIZED


def test_rule_takes_precedence_over_pfc():
    rules = [
        Rule(
            id="r1",
            match_type=MatchType.CONTAINS,
            pattern="starbucks",
            category=Category.ENTERTAINMENT,
            priority=100,
        )
    ]
    cat, src = categorize(_txn(merchant="Starbucks #123", pfc_primary="FOOD_AND_DRINK"), rules)
    assert cat == Category.ENTERTAINMENT
    assert src == CategorySource.RULE


def test_lower_priority_number_wins():
    rules = [
        Rule(id="r_generic", match_type=MatchType.CONTAINS, pattern="amazon",
             category=Category.SHOPPING, priority=100),
        Rule(id="r_override", match_type=MatchType.CONTAINS, pattern="amazon",
             category=Category.GROCERIES, priority=10),
    ]
    cat, src = categorize(_txn(merchant="AMAZON GROCERY"), rules)
    assert cat == Category.GROCERIES
    assert src == CategorySource.RULE


def test_falls_back_to_pfc_then_default():
    cat, src = categorize(_txn(merchant="Shell", pfc_primary="TRANSPORTATION"), [])
    assert (cat, src) == (Category.TRANSPORT, CategorySource.PFC)

    cat, src = categorize(_txn(merchant="Mystery"), [])
    assert (cat, src) == (Category.UNCATEGORIZED, CategorySource.DEFAULT)


def test_rule_matches_raw_name_when_merchant_blank():
    rules = [Rule(id="r1", match_type=MatchType.CONTAINS, pattern="netflix",
                  category=Category.ENTERTAINMENT, priority=50)]
    cat, _ = categorize(_txn(merchant="", raw="NETFLIX.COM"), rules)
    assert cat == Category.ENTERTAINMENT


def test_apply_categorization_returns_copy():
    txn = _txn(merchant="Shell", pfc_primary="TRANSPORTATION")
    out = apply_categorization(txn, [])
    assert out.category == Category.TRANSPORT
    assert txn.category == Category.UNCATEGORIZED  # original unchanged


def test_make_override_rule():
    rule = make_override_rule("Trader Joe's", Category.GROCERIES)
    assert rule.match_type == MatchType.EQUALS
    assert rule.pattern == "Trader Joe's"
    assert rule.priority == 10
    assert rule.matches("trader joe's")
