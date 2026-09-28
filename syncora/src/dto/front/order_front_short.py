from typing import NotRequired, TypedDict


class OrderFrontShort(TypedDict):
    orderId: NotRequired[str]
    customerName: NotRequired[str]
    orderNumber: str
    orderDate: str
    orderTitle: str
