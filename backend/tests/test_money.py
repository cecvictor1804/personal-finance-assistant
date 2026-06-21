from decimal import Decimal

from app.domain.money import (
    format_cents,
    from_cents,
    from_plaid_amount,
    is_inflow,
    is_outflow,
    to_cents,
)


def test_to_cents_rounds_half_up():
    assert to_cents(12.34) == 1234
    assert to_cents("0.005") == 1  # half-up
    assert to_cents(Decimal("99.99")) == 9999
    assert to_cents(0) == 0


def test_to_cents_avoids_float_error():
    # 0.1 + 0.2 == 0.30000000000000004 in float; Decimal path must give exactly 30.
    assert to_cents(0.1 + 0.2) == 30


def test_from_plaid_amount_flips_sign():
    # Plaid: positive amount = money OUT (a purchase). Internal: negative = outflow.
    assert from_plaid_amount(12.34) == -1234
    # Plaid negative = money IN (refund/deposit). Internal positive = inflow.
    assert from_plaid_amount(-50.00) == 5000


def test_from_cents_and_format():
    assert from_cents(-1234) == Decimal("-12.34")
    assert format_cents(-1234, "USD") == "-$12.34"
    assert format_cents(5000, "USD") == "$50.00"


def test_in_out_flow_helpers():
    assert is_outflow(-100) and not is_inflow(-100)
    assert is_inflow(100) and not is_outflow(100)
    assert not is_inflow(0) and not is_outflow(0)
