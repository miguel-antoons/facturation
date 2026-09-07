"""TC-DATE-* and TC-LOCK-* : date formatting and lock/undeletable semantics.

Pure-logic tests on ``OrderBack`` constructed directly (§5.4, §5.5, §2.5.2).
"""

import pytest

from constants.order_back import (
    PEPPOL_DELIVERY_STATUS_NOT_SENT,
    OrderBack,
)
from utils.generic_error import SyncoraError


def order(
    *,
    order_date: str = "2026-09-06",
    delivery_date: str = "2026-09-06",
    external_id: int | None = 0,
    peppol_status: int | None = PEPPOL_DELIVERY_STATUS_NOT_SENT,
    about_invoice_number: str | None = None,
) -> OrderBack:
    data: dict[str, object] = {
        "orderNumber": "2026000001",
        "orderDate": order_date,
        "deliveryDate": delivery_date,
        "expiryDate": "2026-09-20",
    }
    if external_id is not None:
        data["externalId"] = external_id
    if peppol_status is not None:
        data["peppolDeliveryStatus"] = peppol_status
    if about_invoice_number is not None:
        data["aboutInvoiceNumber"] = about_invoice_number
    return OrderBack.model_validate(data, by_name=True)


# --- Dates (TC-DATE-*) --------------------------------------------------- #
def test_formatted_order_date_iso_to_ddmmyyyy() -> None:
    # TC-DATE-1
    assert order(order_date="2026-09-06").formatted_order_date == "06/09/2026"


def test_formatted_order_date_empty_string() -> None:
    # TC-DATE-2
    assert order(order_date="").formatted_order_date == ""


def test_credit_note_formatted_delivery_date_is_empty() -> None:
    # FR-CN-6 : even with a deliveryDate set, cnotes return ""
    cnote = order(about_invoice_number="2026-001", delivery_date="2026-09-06")
    assert cnote.formatted_delivery_date == ""


# --- Locking (TC-LOCK-*) ------------------------------------------------- #
def test_locked_when_external_id_positive() -> None:
    # TC-LOCK-1
    o = order(external_id=42)
    assert o.locked is True
    assert o.billit_sent is True


def test_not_locked_when_external_id_zero() -> None:
    # TC-LOCK-2
    o = order(external_id=0)
    assert o.locked is False
    assert o.billit_sent is False


def test_locked_raises_when_external_id_undefined() -> None:
    # TC-LOCK-3 / TC-GAP-7 : externalId Undefined -> SyncoraError 906
    o = OrderBack.model_validate({"orderNumber": "2026000001"}, by_name=True)
    with pytest.raises(SyncoraError) as exc:
        _ = o.locked
    assert exc.value.error_code == 906


@pytest.mark.parametrize("status", [0, 1, 2])
def test_undeletable_when_peppol_status_not_not_sent(status: int) -> None:
    # TC-LOCK-4 : 0/1/2 are undeletable
    assert order(peppol_status=status).undeletable is True


def test_deletable_when_peppol_status_not_sent() -> None:
    # TC-LOCK-5
    assert order(peppol_status=PEPPOL_DELIVERY_STATUS_NOT_SENT).undeletable is False


def test_undeletable_raises_when_peppol_status_undefined() -> None:
    # TC-LOCK-6 / TC-GAP-7 : peppolDeliveryStatus Undefined -> SyncoraError 906
    o = OrderBack.model_validate({"orderNumber": "2026000001"}, by_name=True)
    with pytest.raises(SyncoraError) as exc:
        _ = o.undeletable
    assert exc.value.error_code == 906


def test_locked_but_still_deletable() -> None:
    # TC-LOCK-7 : externalId>0 (locked) but peppol status -1 (deletable)
    o = order(
        external_id=42,
        peppol_status=PEPPOL_DELIVERY_STATUS_NOT_SENT,
    )
    assert o.locked is True
    assert o.undeletable is False
