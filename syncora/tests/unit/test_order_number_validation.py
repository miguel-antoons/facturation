"""Validation of ``BillBack.orderNumber`` : digits-only rule.

``BillBack`` rejects any ``orderNumber`` that contains non-digit characters
(the frontend's ``"2026-1"`` format included). This closes the OGM crash
documented in ``tests/findings.md`` §1 at the model boundary: since the OGM
check digit is ``int(orderNumber)``, a non-digit number can no longer reach
``ogm``. Empty and unset numbers are still allowed (a bill gets its number
later, §3.1 / TC-BILL-6); credit notes are unaffected (no OGM).
"""

import pytest
from pydantic import ValidationError

from constants.all import SyncoraUndefined, Undefined
from constants.bill_back import BillBack
from constants.cnote_back import CnoteBack


def test_digit_order_number_is_accepted() -> None:
    order = BillBack(orderNumber="2026001")
    assert order.orderNumber == "2026001"


def test_non_digit_order_number_is_rejected() -> None:
    # The frontend's invoice-number format "2026-001" must not validate.
    with pytest.raises(ValidationError, match="numerical digits"):
        BillBack(orderNumber="2026-001")


def test_non_digit_order_number_rejects_frontend_format() -> None:
    # The exact format from TC-OGM-1 ("2026-1") that used to crash ogm.
    with pytest.raises(ValidationError, match="numerical digits"):
        BillBack(orderNumber="2026-1")


def test_empty_order_number_is_allowed() -> None:
    # TC-BILL-6 : orderNumber may be null/empty on create.
    order = BillBack(orderNumber="")
    assert order.orderNumber == ""


def test_unset_order_number_stays_undefined() -> None:
    # A bill constructed without a number keeps the Undefined sentinel,
    # so the validator must not reject the default either.
    order = BillBack()
    assert isinstance(order.orderNumber, Undefined)
    assert order.orderNumber == SyncoraUndefined


def test_cnote_order_number_is_not_restricted() -> None:
    # Credit-note numbers ("C2026-001") are outside the digits-only rule:
    # only bills compute an OGM from their number.
    cnote = CnoteBack(orderNumber="C2026-001")
    assert cnote.orderNumber == "C2026-001"
