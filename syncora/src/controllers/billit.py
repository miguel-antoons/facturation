import base64
from typing import TYPE_CHECKING, Any

import requests
from dotenv import dotenv_values
from requests import Response

from constants.all import RESPONSE_ERROR, RESPONSE_SUCCESS
from dto.external import BillitPDF, OrderBillit
from dto.front import ResponseMessage

if TYPE_CHECKING:
    from collections.abc import Callable

    from dto.back import CustomerBack, OrderBack


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
        "Transporttype": "Peppol",
    }
    return requests.post(url, headers=headers, json=payload)  # noqa: S113


def send_billit(
    order_data: OrderBack[Any, Any],
    pdf_bytes: bytes,
    customer_data: CustomerBack,
    *,
    callback: Callable[[Response], Any],
) -> ResponseMessage:
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
        return ResponseMessage(status=RESPONSE_SUCCESS)
    print(response.text)
    return ResponseMessage(status=RESPONSE_ERROR, message=response.json())
