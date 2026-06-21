from datetime import date

from app.adapters.fake_provider import plaid_account, plaid_txn
from app.domain.categories import Category, map_pfc
from app.services.normalize import normalize_account, normalize_transaction, transaction_country


def test_normalize_transaction_sign_and_fields():
    raw = plaid_txn(
        transaction_id="tx1",
        account_id="acc9",
        name="SQ *COFFEE",
        merchant_name="Blue Bottle",
        amount=4.50,
        date="2026-02-03",
        pfc_primary="FOOD_AND_DRINK",
        pfc_detailed="FOOD_AND_DRINK_COFFEE",
    )
    txn = normalize_transaction(raw)
    assert txn.id == "plaid_tx1"
    assert txn.account_id == "acc9"
    assert txn.amount_cents == -450  # outflow
    assert txn.merchant == "Blue Bottle"
    assert txn.raw_name == "SQ *COFFEE"
    assert txn.date == date(2026, 2, 3)
    assert txn.plaid_txn_id == "tx1"
    assert txn.pfc_primary == "FOOD_AND_DRINK"


def test_normalize_transaction_falls_back_to_name_for_merchant():
    raw = plaid_txn(transaction_id="tx2", name="WHOLE FOODS", amount=20.0)
    assert normalize_transaction(raw).merchant == "WHOLE FOODS"


def test_normalize_marks_transfers():
    raw = plaid_txn(transaction_id="tx3", amount=100.0, pfc_primary="TRANSFER_OUT")
    txn = normalize_transaction(raw)
    assert txn.is_transfer is True
    assert map_pfc("TRANSFER_OUT") == Category.TRANSFER


def test_transaction_country():
    raw = plaid_txn(transaction_id="tx4", amount=1.0, location_country="GB")
    assert transaction_country(raw) == "GB"


def test_normalize_account_liability_detection():
    credit = plaid_account(account_id="c1", name="Visa", type="credit", balance=523.10)
    acct = normalize_account(credit)
    assert acct.is_liability is True
    assert acct.is_asset is False
    assert acct.balance_cents == 52310

    checking = plaid_account(account_id="d1", name="Checking", type="depository", balance=1000.0)
    assert normalize_account(checking).is_asset is True
