"""TC-OGM-* : structured communication (OGM) generation (§5.6).

The OGM is derived from ``orderNumber`` by left-padding to 10 chars with '0',
taking ``int(first10) % 97`` (97 when 0) and formatting as
``+++ddd/dddd/ddddCC+++``. Credit notes return an empty string.
"""

import pytest
from pydantic import ValidationError

from dto.back import BillBack


def ogm_for(number: str) -> str:
    order = BillBack(orderNumber=number)
    return order.ogm


def test_ogm_short_number_is_padded() -> None:
    # TC-OGM-1 : shorter than 10 digits is right-padded with '0'
    assert ogm_for("123") == "+++123/0000/00036+++"


def test_ogm_exactly_ten_digits() -> None:
    # TC-OGM-2 : no extra padding
    assert ogm_for("9999999999") == "+++999/9999/99948+++"


def test_ogm_check_digit_zero_becomes_97() -> None:
    # TC-OGM-4 : int(padded10) % 97 == 0 is stored as 97
    assert ogm_for("0000000000") == "+++000/0000/00097+++"


def test_ogm_longer_than_ten_chars_drops_overflow() -> None:
    # TC-OGM-3 [ASSUMPTION] : ljust only pads; the first 10 chars are used and
    # any extra chars are dropped from the formatted OGM.
    assert ogm_for("12345678901") == "+++123/4567/89020+++"


def test_ogm_non_digit_order_number_unreachable() -> None:
    """Former findings.md §1 gap, now closed at the model boundary.

    The spec's TC-OGM-1 example uses ``"2026-1"`` (the frontend's invoice-number
    format), and ``int("2026-10000")`` would fail because of the hyphen.
    ``BillBack`` now rejects non-digit orderNumbers at validation time, so
    ``ogm`` can no longer crash on them. See
    ``tests/unit/test_order_number_validation.py``.
    """
    with pytest.raises(ValidationError, match="numerical digits"):
        _ = ogm_for("2026-1")
