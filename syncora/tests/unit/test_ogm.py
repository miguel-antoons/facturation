"""TC-OGM-* : structured communication (OGM) generation (§5.6).

The OGM is derived from ``orderNumber`` by left-padding to 10 chars with '0',
taking ``int(first10) % 97`` (97 when 0) and formatting as
``+++ddd/dddd/ddddCC+++``. Credit notes return an empty string.

Note: see ``tests/findings.md`` -- the implementation crashes when the
orderNumber contains non-digit characters (e.g. the frontend's ``"2026-1"``
format). The Sunny cases below use digit-only numbers; the crash is pinned
separately as a known gap.
"""

import pytest

from constants.order_back import OrderBack


def ogm_for(number: str) -> str:
    order = OrderBack(orderNumber=number)
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


def test_ogm_credit_note_is_empty() -> None:
    # TC-OGM-5 : credit notes have no OGM
    order = OrderBack(orderNumber="2026000001", aboutInvoiceNumber="2026-001")
    assert order.ogm == ""
    assert order.is_cnote


@pytest.mark.gap
def test_ogm_non_digit_order_number_crashes() -> None:
    """Pinned gap: OGM raises ValueError for non-digit orderNumbers.

    The spec's TC-OGM-1 example uses ``"2026-1"`` (the frontend's invoice-number
    format), but ``int("2026-10000")`` fails because of the hyphen. OGM is
    therefore broken for any real orderNumber that is not pure digits. See
    ``tests/findings.md``.
    """
    with pytest.raises(ValueError):
        _ = ogm_for("2026-1")
