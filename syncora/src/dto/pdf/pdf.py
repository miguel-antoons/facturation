from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from .customer_pdf import CustomerPDF
    from .order_line_pdf import OrderLinePDF
    from .order_pdf import OrderPDF


class PDF(TypedDict):
    id: NotRequired[str]
    Order: OrderPDF
    Customer: CustomerPDF
    OrderLines: list[OrderLinePDF]
