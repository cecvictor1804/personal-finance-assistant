from datetime import date

from app.domain.models import Transaction, TransactionSource
from app.services.dedup import find_duplicate, merchant_similarity


def _manual(id_, merchant, amount=-4000, d=date(2026, 1, 10)) -> Transaction:
    return Transaction(
        id=id_, account_id="a1", amount_cents=amount, date=d,
        merchant=merchant, source=TransactionSource.MANUAL,
    )


def _plaid(merchant, amount=-4000, d=date(2026, 1, 11)) -> Transaction:
    return Transaction(
        id="plaid_x", account_id="a1", amount_cents=amount, date=d,
        merchant=merchant, source=TransactionSource.PLAID,
    )


def test_merchant_similarity():
    assert merchant_similarity("Joe's Diner", "joes diner") == 1.0
    assert merchant_similarity("Starbucks", "Starbucks #4412") == 1.0  # substring
    assert merchant_similarity("Apple", "Microsoft") < 0.5
    assert merchant_similarity("", "anything") == 0.0


def test_flags_close_match():
    candidates = [_manual("m1", "Joe's Diner")]
    dup = find_duplicate(_plaid("JOES DINER"), candidates)
    assert dup == "m1"


def test_no_flag_when_merchant_differs():
    candidates = [_manual("m1", "Whole Foods")]
    assert find_duplicate(_plaid("Shell Gas"), candidates) is None


def test_empty_merchant_flags_on_amount_date_alone():
    # When one side has no merchant, amount+date match (already pre-filtered) is enough to flag.
    candidates = [_manual("m1", "")]
    assert find_duplicate(_plaid("Some Cafe"), candidates) == "m1"


def test_picks_best_of_several_candidates():
    candidates = [_manual("m1", "Cafe Bla"), _manual("m2", "Joe's Diner")]
    assert find_duplicate(_plaid("Joes Diner"), candidates) == "m2"
