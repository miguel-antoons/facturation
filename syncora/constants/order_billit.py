from typing import TypedDict

from constants.customer_back import CustomerBack
from constants.customer_billit import CustomerBillit
from constants.order_back import OrderBack

ORDER_TYPE_INVOICE = "Invoice"
ORDER_TYPE_CREDIT_NOTE = "CreditNote"
ORDER_DIRECTION_INCOME = "Income"



# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR BILLIT API
# * ------------------------------------------

class BillitPDF(TypedDict):
    FileName: str
    FileContent: str


class OrderBillit(OrderBack):
    Customer: CustomerBillit
    OrderType: str
    OrderDirection: str
    OrderPDF: BillitPDF


# * ------------------------------------------
# * CONVERSION FUNCTIONS
# * ------------------------------------------
def order_from_back(order_back: OrderBack, customer_back: CustomerBack) -> OrderBillit:
    res = OrderBillit(
        Customer=CustomerBillit(**customer_back.model_dump()).model_dump(),
        OrderType=ORDER_TYPE_INVOICE,
        OrderDirection=ORDER_DIRECTION_INCOME,
        OrderNumber=order_back["OrderNumber"],
        OrderDate=order_back["OrderDate"],
        ExpiryDate=order_back["ExpiryDate"],
        DeliveryDate=order_back["DeliveryDate"],
        OrderTitle=order_back["OrderTitle"],
        OrderLines=order_back.get("OrderLines", []),
        VentilationCode=order_back["VentilationCode"],
    )

    if "OrderID" in order_back:
        res["OrderID"] = order_back["OrderID"]
    return res
