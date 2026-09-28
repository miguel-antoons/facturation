from typing import TYPE_CHECKING, NotRequired, TypedDict

if TYPE_CHECKING:
    from .order_line_db import OrderLineDB


class OrderDB(TypedDict):
    _id: NotRequired[str]
    customerId: NotRequired[int]
    orderNumber: str
    orderDate: str
    expiryDate: str
    orderTitle: str
    orderLines: NotRequired[list[OrderLineDB]]
    ventilationCode: NotRequired[str]
    peppolDeliveryStatus: NotRequired[int]
