from typing import TypedDict, NotRequired


PEPPOL_DELIVERY_STATUS_NOT_SENT = -1
PEPPOL_DELIVERY_STATUS_UNKNOWN = 0
PEPPOL_DELIVERY_STATUS_PENDING = 1
PEPPOL_DELIVERY_STATUS_SENT = 2

ORDER_BACK_ORDER_ID = "OrderID"
ORDER_BACK_PEPPOL_DELIVERY_STATUS = "PeppolDeliveryStatus"


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR DATABASE
# * ------------------------------------------
class OrderLineBack(TypedDict):
    Description: str
    Quantity: float | int
    UnitPriceExcl: float
    Unit: str
    VATPercentage: float


class OrderBack(TypedDict):
    _id: NotRequired[str]
    OrderID: NotRequired[int]
    CustomerId: NotRequired[int]
    OrderNumber: str
    OrderDate: str
    ExpiryDate: str
    DeliveryDate: str
    OrderTitle: str
    OrderLines: NotRequired[list[OrderLineBack]]
    VentilationCode: NotRequired[str]
    AboutInvoiceNumber: NotRequired[str]
    PeppolDeliveryStatus: NotRequired[int]
