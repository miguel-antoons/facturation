import base64
from typing import TYPE_CHECKING, Any

import requests
from dotenv import dotenv_values
from flask import jsonify
from requests import Response

from constants.all import RESPONSE_ERROR, RESPONSE_SUCCESS, ResponseMessage
from constants.order_billit import BillitPDF, OrderBillit
from constants.order_pdf import PDF, CustomerPDF, OrderLinePDF, OrderPDF
from pdf.static_data import comments

if TYPE_CHECKING:
    from collections.abc import Callable

    from constants.customer_back import CustomerBack
    from constants.order_back import OrderBack, _OrderLineBack


def format_dyn_data(
    order_data: OrderBack,
    customer_data: CustomerBack,
    *,
    set_id: bool = False,
    number_formatter: Callable[[int | float], str] = lambda n: n,
    order_lines_formater: Callable[[_OrderLineBack], OrderLinePDF] = lambda d: d,
) -> PDF:
    result = PDF(
        Order=OrderPDF(
            OrderNumber=order_data.orderNumber,
            AboutInvoiceNumber=order_data.aboutInvoiceNumber or "",
            OrderDate=order_data.formatted_order_date,
            DeliveryDate=order_data.formatted_delivery_date,
            ExpiryDate=order_data.formatted_expiry_date,
            OrderTitle=order_data.orderTitle,
            YourReference=order_data.orderNumber,
            VAT=number_formatter(order_data.orderLines[0].VATPercentage),
            TotalExcl=number_formatter(order_data.total_excl),
            TotalVAT=number_formatter(order_data.total_vat),
            TotalIncl=number_formatter(order_data.total_incl),
            Comments="",
            LegalInfo=comments[customer_data.language.upper()][
                order_data.ventilationCode
            ],
            OGM=order_data.ogm,
        ),
        Customer=CustomerPDF(
            OfficialCompanyName=customer_data.company or "",
            ContactFullName=(
                f"{customer_data.name or ''} {customer_data.surname or ''}".strip()
            ),
            Salutation=customer_data.salutation,
            StreetAndNumber=f"{customer_data.street} {customer_data.number}".strip(),
            ZipCode=customer_data.postal_code,
            City=customer_data.city,
            CountryName="",
            VAT=customer_data.vat_number,
            Nr=customer_data.id,
        ),
        OrderLines=list(map(order_lines_formater, order_data.orderLines)),
    )

    if set_id:
        result["id"] = order_data.orderId

    return result


def get_headers() -> dict[str, str]:
    return {
        "accept": "application/json",
        "apiKey": dotenv_values(".env")["API_SECRET"] or "",
        "partyID": dotenv_values(".env")["PARTY_ID"] or "",
        "contextPartyID": dotenv_values(".env")["PARTY_ID"] or "",
    }


def delete_order(order_id: int) -> ResponseMessage | None:
    url = f"{dotenv_values(".env")["URL"]}/orders/{order_id}"
    headers = get_headers()
    response = requests.delete(url, headers=headers)  # noqa: S113
    if response.content != b"true":
        print(response.text)
    return (
        None
        if response.content == b"true"
        else ResponseMessage(status=RESPONSE_ERROR, message=response.text)
    )


def send_peppol(order_id: int) -> Response:
    url = f"{dotenv_values('.env')['URL']}/orders/commands/send"
    headers = get_headers()
    payload = {
        "OrderIDs": [order_id],
        "SendMethod": "Peppol",
    }
    return requests.post(url, headers=headers, json=payload)  # noqa: S113


def send_billit(
    order_data: OrderBack,
    pdf_bytes: bytes,
    customer_data: CustomerBack,
    *,
    callback: Callable[[Response], Any],
) -> Response:
    raw_data = order_data.model_dump()
    raw_data["Customer"] = customer_data.model_dump()
    base64_pdf = base64.b64encode(pdf_bytes)
    raw_data["OrderPDF"] = BillitPDF(
        FileName=f"bill_{customer_data.name}_{customer_data.surname}_{customer_data.company}_{order_data.orderNumber}.pdf",
        FileContent=base64_pdf.decode("utf-8"),
    )
    payload: OrderBillit = OrderBillit.model_validate(raw_data, extra="allow")

    headers = get_headers()
    url = f"{dotenv_values(".env")['URL']}/orders"
    response = requests.post(  # noqa: S113
        url, headers=headers, json=payload.model_dump()
    )

    if response.status_code in [200, 201]:
        callback(response)
        return jsonify(ResponseMessage(status=RESPONSE_SUCCESS))
    print(response.text)
    return jsonify(ResponseMessage(status=RESPONSE_ERROR, message=response.json()))
