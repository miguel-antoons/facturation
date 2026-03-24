from collections.abc import Callable

from dateutil import parser
from dotenv import dotenv_values

from constants.order_pdf import calculate_order_totals, ogm_gen, PDF, OrderPDF, CustomerPDF, OrderLinePDF
from pdf.static_data import comments

from constants.order_back import *
from constants.customer import *


def format_dyn_data(
    order_data: OrderBack,
    customer_data: CustomerBack,
    *,
    set_id: bool = False,
    number_formatter: Callable[[int | float], int | str] = lambda n: n,
    order_lines_formater: Callable[[OrderLineBack], OrderLinePDF] = lambda d: d,
    is_cnote: bool = False,
) -> PDF:
    totals = calculate_order_totals(order_data["OrderLines"])
    total_excl = totals["TotalExcl"]
    total_incl = totals["TotalIncl"]
    result = PDF(
        Order=OrderPDF(
            OrderNumber=order_data["OrderNumber"],
            AboutInvoiceNumber=order_data.get("AboutInvoiceNumber", ""),
            OrderDate=parser.parse(order_data["OrderDate"]).strftime("%d/%m/%Y"),
            DeliveryDate=parser.parse(order_data["DeliveryDate"]).strftime("%d/%m/%Y") if not is_cnote else "",
            ExpiryDate=parser.parse(order_data["ExpiryDate"]).strftime("%d/%m/%Y"),
            OrderTitle=order_data["OrderTitle"],
            YourReference=order_data['OrderNumber'],
            VAT=number_formatter(order_data["OrderLines"][0]["VATPercentage"]),
            TotalExcl=number_formatter(total_excl),
            TotalVAT=number_formatter(total_incl - total_excl),
            TotalIncl=number_formatter(total_incl),
            Comments="",
            LegalInfo=comments[customer_data.language.upper()][order_data["VentilationCode"]],
            OGM=ogm_gen(order_data["OrderNumber"]) if not is_cnote else "",
        ),
        Customer=CustomerPDF(
            OfficialCompanyName=customer_data.company or "",
            ContactFullName=f"{customer_data.last_name or ''} {customer_data.first_name or ''}".strip(),
            Salutation=customer_data.name_prefix,
            StreetAndNumber=f"{customer_data.street} {customer_data.street_number}".strip(),
            ZipCode=customer_data.postal_code,
            City=customer_data.city,
            CountryName="",
            VAT=customer_data.vat_number,
            Nr=customer_data.id,
        ),
        OrderLines=list(map(order_lines_formater, order_data["OrderLines"])),
    )

    if set_id:
        result["id"] = order_data["_id"]

    return result


def order_locked(order_data: OrderBack) -> bool:
    return order_data.get(ORDER_BACK_ORDER_ID, 0) != 0


def bill_undeletable(order_data: OrderBack) -> bool:
    return order_data.get(ORDER_BACK_PEPPOL_DELIVERY_STATUS, PEPPOL_DELIVERY_STATUS_NOT_SENT) != PEPPOL_DELIVERY_STATUS_NOT_SENT


def get_headers():
    return {
        "accept": "application/json",
        "apiKey": dotenv_values(".env")["API_SECRET"],
        "partyID": dotenv_values(".env")["PARTY_ID"],
        "contextPartyID": dotenv_values(".env")["PARTY_ID"]
    }
