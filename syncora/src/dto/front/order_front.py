from typing import TYPE_CHECKING, NotRequired

from .order_front_short import OrderFrontShort

if TYPE_CHECKING:
    from .order_line_front import OrderLineFront


class OrderFront(OrderFrontShort):
    customerId: int
    expiryDate: str
    deliveryDate: str
    orderLines: list[OrderLineFront]
    ventilationCode: str
    aboutInvoiceNumber: NotRequired[str]
    billitSent: bool
    peppolStatus: NotRequired[int]
