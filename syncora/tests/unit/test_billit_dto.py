"""Billit DTO mapping unit tests (TC-BILLIT-17/18/22/23/24/25/26/27).

These build the ``OrderBillit`` / ``CustomerBillit`` pydantic models directly
and assert on the outbound JSON shape -- no Flask, no HTTP. The full send flow
(POST /orders body, headers, PDF attachment) is covered in
``tests/api/test_billit_flow.py``.
"""

import pytest

from constants.customer_billit import CustomerBillit
from constants.order_back import OrderBack
from constants.order_billit import (
    ORDER_DIRECTION_INCOME,
    ORDER_TYPE_CREDIT_NOTE,
    ORDER_TYPE_INVOICE,
    OrderBillit,
)
from tests.helpers import make_bill_payload, make_customer_back
from utils.generic_error import SyncoraError


def _order_billit(
    *,
    about_invoice_number: str | None = None,
    customer: object | None = None,
) -> OrderBillit:
    payload = dict(make_bill_payload())
    if about_invoice_number is not None:
        payload["aboutInvoiceNumber"] = about_invoice_number
    order = OrderBack.model_validate(payload, by_name=True)
    cust = customer or make_customer_back()
    raw = order.model_dump()
    raw["Customer"] = cust.model_dump()
    raw["OrderPDF"] = {"FileName": "bill.pdf", "FileContent": "ZmFrZQ=="}
    return OrderBillit.model_validate(raw, extra="allow")


# --- OrderType / OrderDirection (TC-BILLIT-17, TC-BILLIT-18) ------------- #
def test_order_type_is_invoice_for_bills() -> None:
    assert _order_billit().OrderType == ORDER_TYPE_INVOICE


def test_order_type_is_credit_note_for_cnotes() -> None:
    assert (
        _order_billit(about_invoice_number="2026-001").OrderType
        == ORDER_TYPE_CREDIT_NOTE
    )


def test_order_direction_is_always_income() -> None:
    assert _order_billit().OrderDirection == ORDER_DIRECTION_INCOME


# --- Credit-note amounts stay positive (TC-BILLIT-22) ------------------- #
def test_credit_note_totals_are_non_negative() -> None:
    payload = _order_billit(about_invoice_number="2026-001")
    assert payload.TotalExcl >= 0
    assert payload.TotalIncl >= 0
    assert payload.TotalVAT >= 0


# --- Customer payload (TC-BILLIT-23/25/26/27) --------------------------- #
def test_customer_addresses_contains_full_invoice_address() -> None:
    # TC-BILLIT-23
    cb = CustomerBillit.model_validate(make_customer_back().model_dump())
    addr = cb.Addresses[0]
    assert addr["Street"] == "Rue X"
    assert addr["StreetNumber"] == "12"
    assert addr["City"] == "Bruxelles"
    assert addr["Zipcode"] == "1000"
    assert addr["CountryCode"] == "BE"
    assert addr["AddressType"] == "InvoiceAddress"


def test_country_code_is_always_be() -> None:
    # TC-BILLIT-25 [GAP] : hardcoded, no country input exists
    cb = CustomerBillit.model_validate(make_customer_back().model_dump())
    assert cb.CountryCode == "BE"


def test_language_is_uppercased_in_billit_payload() -> None:
    # TC-BILLIT-27
    cb = CustomerBillit.model_validate(make_customer_back(language="fr").model_dump())
    assert cb.Language == "FR"


def test_multiple_emails_and_phones_collapse_to_first_value() -> None:
    # TC-BILLIT-26
    cust = make_customer_back(
        comment="a@b.com c@d.com 0475123456 0485987654 010/22 33 44",
    )
    cb = CustomerBillit.model_validate(cust.model_dump())
    assert cb.Email == "a@b.com"
    assert cb.Mobile == "0475123456"
    assert cb.Phone == "010223344"


def test_customer_without_any_name_raises_syncora_error_900() -> None:
    # TC-BILLIT-24 : missing company/name/surname -> SyncoraError 900
    cust = make_customer_back(name=None, surname=None, company=None, vat_number=None)
    with pytest.raises(SyncoraError) as exc:
        CustomerBillit.model_validate(cust.model_dump())
    assert exc.value.error_code == 900
