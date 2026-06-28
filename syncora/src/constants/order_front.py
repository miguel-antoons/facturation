from typing import NotRequired, TypedDict


class OrderLineFront(TypedDict):
    description: str
    quantity: float
    unitPriceExcl: float
    unit: str
    VATPercentage: float


class OrderFrontShort(TypedDict):
    orderId: NotRequired[str]
    customerName: NotRequired[str]
    orderNumber: str
    orderDate: str
    orderTitle: str


class OrderFront(OrderFrontShort):
    customerId: int
    expiryDate: str
    deliveryDate: str
    orderLines: list[OrderLineFront]
    ventilationCode: str
    aboutInvoiceNumber: NotRequired[str]
    billitSent: bool
    peppolStatus: NotRequired[int]
