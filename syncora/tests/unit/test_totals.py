"""TC-TOTAL-* : taxable-amount totals (§5.5).

Pure-logic tests on ``OrderBack`` constructed directly. The order totals use
the Billit taxable-amount method: lines are grouped by VAT rate, the unrounded
excl amount is summed per group, VAT is applied per group, and rounding happens
once per group.
"""

import pytest

from tests.unit.helpers import line, order_with_lines


def test_total_single_line_6pct() -> None:
    # TC-TOTAL-1 : qty 1, price 100, VAT 6%
    order = order_with_lines(
        [{"quantity": 1, "unitPriceExcl": 100.0, "VATPercentage": 6.0}]
    )
    assert order.total_excl == 100.00
    assert order.total_incl == 106.00
    assert order.total_vat == 6.00


def test_total_two_lines_same_rate_21pct() -> None:
    # TC-TOTAL-2 : 100 + 200 at 21%
    order = order_with_lines(
        [
            {"quantity": 1, "unitPriceExcl": 100.0, "VATPercentage": 21.0},
            {"quantity": 1, "unitPriceExcl": 200.0, "VATPercentage": 21.0},
        ]
    )
    assert order.total_excl == 300.00
    assert order.total_incl == 363.00
    assert order.total_vat == 63.00


def test_total_two_lines_different_rates() -> None:
    # TC-TOTAL-3 : 6% 100 and 21% 100 -> grouped rounding
    order = order_with_lines(
        [
            {"quantity": 1, "unitPriceExcl": 100.0, "VATPercentage": 6.0},
            {"quantity": 1, "unitPriceExcl": 100.0, "VATPercentage": 21.0},
        ]
    )
    assert order.total_excl == 200.00
    assert order.total_incl == round(100 * 1.06, 2) + round(100 * 1.21, 2)
    assert order.total_incl == 227.00
    assert order.total_vat == 27.00


def test_total_rounding_drift_three_6pct_lines() -> None:
    # TC-TOTAL-4 : three 6% lines of 33.33 each (grouped, not per-line)
    order = order_with_lines(
        [{"quantity": 1, "unitPriceExcl": 33.33, "VATPercentage": 6.0}] * 3
    )
    assert order.total_excl == round(99.99, 2)
    assert order.total_incl == round(99.99 * 1.06, 2)
    assert order.total_incl == 105.99


def test_total_zero_vat_reverse_charge() -> None:
    # TC-TOTAL-5 : ventilation code 21 (reverse charge), 0% VAT
    order = order_with_lines(
        [{"quantity": 1, "unitPriceExcl": 100.0, "VATPercentage": 0.0}],
        ventilation_code="21",
    )
    assert order.total_vat == 0.00
    assert order.total_incl == order.total_excl


def test_total_empty_order_lines() -> None:
    # TC-TOTAL-6 : no lines
    order = order_with_lines([])
    assert order.total_excl == 0.00
    assert order.total_incl == 0.00
    assert order.total_vat == 0.00


def test_total_negative_raises() -> None:
    # TC-TOTAL-7 : negative computed total surfaces a SyncoraError (903-905)
    from utils.generic_error import SyncoraError

    order = order_with_lines(
        [{"quantity": 1, "unitPriceExcl": -50.0, "VATPercentage": 6.0}]
    )
    with pytest.raises(SyncoraError):
        _ = order.total_excl
    with pytest.raises(SyncoraError):
        _ = order.total_incl


def test_per_line_total_excl_is_line_rounded() -> None:
    # TC-TOTAL-8 : each line total_excl == round(qty*price, 2)
    ln = line(quantity=3, price=33.33)
    assert ln.total_excl == round(3 * 33.33, 2)
    assert ln.total_excl == 99.99


def test_total_vat_equals_incl_minus_excl_for_multi_rate() -> None:
    # TC-TOTAL-9 : the identity holds for multi-rate cases. total_vat is the
    # *unrounded* difference of the two 2dp totals (see tests/findings.md), so
    # we assert the exact identity rather than a re-rounded value.
    order = order_with_lines(
        [
            {"quantity": 2, "unitPriceExcl": 50.0, "VATPercentage": 6.0},
            {"quantity": 1, "unitPriceExcl": 123.45, "VATPercentage": 21.0},
            {"quantity": 4, "unitPriceExcl": 9.99, "VATPercentage": 0.0},
        ]
    )
    assert order.total_vat == order.total_incl - order.total_excl


def test_total_excl_is_rounded_sum_of_unrounded_line_excl() -> None:
    # Sanity: total_excl == round(sum of unrounded qty*price, 2), not sum of
    # rounded per-line totals (the taxable-amount method).
    order = order_with_lines(
        [
            {"quantity": 1, "unitPriceExcl": 33.335, "VATPercentage": 6.0},
            {"quantity": 1, "unitPriceExcl": 33.335, "VATPercentage": 6.0},
        ]
    )
    assert order.total_excl == round(33.335 + 33.335, 2)


# `OrderBack` is constructed directly in every test above; no fixtures needed.
