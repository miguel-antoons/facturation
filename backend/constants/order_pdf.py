from typing import TypedDict, NotRequired

from constants.order_back import OrderBack, OrderLineBack


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR PDF GENERATION
# * ------------------------------------------
class OrderPDF(OrderBack):
    YourReference: str
    VAT: str
    TotalExcl: str
    TotalVAT: str
    TotalIncl: str
    Comments: str
    LegalInfo: str
    OGM: str


class CustomerPDF(TypedDict):
    OfficialCompanyName: str
    ContactFullName: str
    Salutation: str
    StreetAndNumber: str
    ZipCode: str
    City: str
    CountryName: str
    VAT: str
    Nr: int


class OrderLinePDF(TypedDict):
    Description: str
    AmountExcl: str
    Quantity: str
    Unit: str
    TotalExcl: str
    VATPercentage: str
    TotalIncl: str


class PDF(TypedDict):
    id: NotRequired[str]
    Order: OrderPDF
    Customer: CustomerPDF
    OrderLines: list[OrderLinePDF]


# * ------------------------------------------
# * CONVERSION FUNCTIONS
# * ------------------------------------------
def price_to_string(price: float) -> str:
    return '{0:.2f}'.format(price).replace(".", ",")


def order_line_string(order_line: OrderLineBack) -> OrderLinePDF:
    return OrderLinePDF(
        Description=order_line["Description"],
        AmountExcl=price_to_string(order_line["UnitPriceExcl"]),
        Quantity=str(order_line["Quantity"]) if isinstance(order_line["Quantity"], int) else price_to_string(order_line["Quantity"]),
        Unit=order_line.get("Unit", ""),
        TotalExcl=price_to_string(order_line_total_excl(order_line["Quantity"], order_line["UnitPriceExcl"])),
        VATPercentage='{0:.0f}'.format(order_line["VATPercentage"]),
        TotalIncl=price_to_string(order_line_total_incl(order_line["Quantity"], order_line["UnitPriceExcl"], order_line["VATPercentage"])),
    )


def calculate_order_totals(order_lines: list[OrderLineBack]) -> dict:
    total_excl = 0.0
    total_incl = 0.0

    for line in order_lines:
        line_total_excl = order_line_total_excl(line["Quantity"], line["UnitPriceExcl"])
        line_total_incl = order_line_total_incl(line["Quantity"], line["UnitPriceExcl"], line["VATPercentage"])

        total_excl += line_total_excl
        total_incl += line_total_incl

    return {
        "TotalExcl": round(total_excl, 2),
        "TotalIncl": round(total_incl, 2),
    }


def ogm_gen(reference: str) -> str:
    ref_numbers = reference.ljust(10, '0')
    check_digit = int(ref_numbers[:10]) % 97
    if check_digit == 0:
        check_digit = 97
    return f"+++{ref_numbers[0:3]}/{ref_numbers[3:7]}/{ref_numbers[7:10]}{str(check_digit).ljust(2, '0')}+++"


def order_line_total_excl(quantity: float, unit_price_excl: float) -> float:
    return quantity * unit_price_excl


def order_line_total_incl(quantity: float, unit_price_excl: float, vat_percentage: float) -> float:
    total_excl = order_line_total_excl(quantity, unit_price_excl)
    vat_amount = total_excl * vat_percentage / 100
    return total_excl + vat_amount
