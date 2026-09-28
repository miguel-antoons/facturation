from typing import TYPE_CHECKING

from dateutil import parser

from dto.pdf import OrderLinePDF

if TYPE_CHECKING:
    from dto.back import OrderLineBack


def format_date(date: str) -> str:
    return parser.parse(date).strftime("%d/%m/%Y") if date else ""


def price_to_string(price: float) -> str:
    return f"{price:.2f}".replace(".", ",")


def order_line_string(order_line: OrderLineBack) -> OrderLinePDF:
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
