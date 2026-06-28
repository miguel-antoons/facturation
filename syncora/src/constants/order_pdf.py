from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from constants.order_back import _OrderLineBack


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR PDF GENERATION
# * ------------------------------------------
class OrderPDF(TypedDict):
    OrderNumber: str
    AboutInvoiceNumber: str
    OrderDate: str
    DeliveryDate: str
    ExpiryDate: str
    OrderTitle: str
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
    return f"{price:.2f}".replace(".", ",")


def order_line_string(order_line: _OrderLineBack) -> OrderLinePDF:
    return OrderLinePDF(
        Description=order_line.description,
        AmountExcl=price_to_string(order_line.unitPriceExcl),
        Quantity=(
            str(order_line.quantity)
            if isinstance(order_line.quantity, int)
            else price_to_string(order_line.quantity)
        ),
        Unit=order_line.unit,
        TotalExcl=price_to_string(order_line.total_excl),
        VATPercentage=f"{order_line.VATPercentage:.0f}",
        TotalIncl=price_to_string(order_line.total_incl),
    )


def order_line_total_excl(quantity: float, unit_price_excl: float) -> float:
    return quantity * unit_price_excl


def order_line_total_incl(
    quantity: float, unit_price_excl: float, vat_percentage: float
) -> float:
    total_excl = order_line_total_excl(quantity, unit_price_excl)
    vat_amount = total_excl * vat_percentage / 100
    return total_excl + vat_amount
