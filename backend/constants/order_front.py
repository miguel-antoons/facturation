from typing import TypedDict, NotRequired

from constants.order_back import OrderBack


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR FRONTEND
# * ------------------------------------------
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


# * ------------------------------------------
# * CONVERSION FUNCTIONS
# * ------------------------------------------
def convert_order_back_to_front(order: OrderBack) -> OrderFront:
    order_lines_front = []
    for line in order['OrderLines']:
        order_lines_front.append(OrderLineFront(
            description=line['Description'] or "",
            quantity=line['Quantity'] or 1,
            unitPriceExcl=line['UnitPriceExcl'] or 0.00,
            unit=line['Unit'] or "",
            VATPercentage=line['VATPercentage'] or "",
        ))

    res: OrderFront = OrderFront(
        customerId=order['CustomerId'],
        orderNumber=order['OrderNumber'],
        orderDate=order['OrderDate'],
        expiryDate=order['ExpiryDate'],
        deliveryDate=order['DeliveryDate'],
        orderTitle=order['OrderTitle'],
        orderLines=order_lines_front,
        ventilationCode=order['VentilationCode'],
        billitSent="OrderID" in order and order['OrderID'] > 0,
        peppolStatus=order['PeppolDeliveryStatus'],
    )

    if 'AboutInvoiceNumber' in order:
        res['aboutInvoiceNumber'] = order['AboutInvoiceNumber']

    return res
