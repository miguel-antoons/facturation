"""Unit-test-local helpers (pure-logic, no Flask/DB/network)."""

from typing import Any

from constants.order_back import OrderBack, _OrderLineBack


def order_with_lines(
    lines: list[dict[str, Any]],
    *,
    order_number: str = "2026-001",
    about_invoice_number: str | None = None,
    external_id: int | None = None,
    peppol_status: int | None = None,
    ventilation_code: str = "2",
) -> OrderBack:
    """Build an ``OrderBack`` directly from line dicts (no validation round-trip)."""
    data: dict[str, Any] = {
        "orderNumber": order_number,
        "ventilationCode": ventilation_code,
        "orderLines": lines,
    }
    if about_invoice_number is not None:
        data["aboutInvoiceNumber"] = about_invoice_number
    if external_id is not None:
        data["externalId"] = external_id
    if peppol_status is not None:
        data["peppolDeliveryStatus"] = peppol_status
    return OrderBack.model_validate(data, by_name=True)


def line(
    quantity: float = 1,
    price: float = 100.0,
    vat: float = 6.0,
    description: str = "Travaux",
) -> _OrderLineBack:
    return _OrderLineBack(
        description=description,
        quantity=quantity,
        unitPriceExcl=price,
        unit="h",
        VATPercentage=vat,
    )
