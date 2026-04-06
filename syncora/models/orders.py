from constants.order_back import *
from constants.order_front import OrderLineFront


def format_order(
    customer_id: int,
    order_number: str,
    order_date: str,
    expiry_date: str,
    delivery_date: str,
    order_title: str,
    order_lines: list[OrderLineFront],
    ventilation_code: str,
    about_invoice: str = None,
    set_order_id: bool = True,
) -> OrderBack:
    formatted_order_lines = []
    for line in order_lines:
        formatted_order_lines.append(OrderLineBack(
            Description=line.get('description'),
            Quantity=line.get('quantity'),
            UnitPriceExcl=line.get('unitPriceExcl'),
            Unit=line.get('unit'),
            VATPercentage=line.get('VATPercentage'),
        ))

    res = OrderBack(
        CustomerId=customer_id,
        OrderNumber=order_number,
        OrderDate=order_date,
        ExpiryDate=expiry_date,
        DeliveryDate=delivery_date,
        OrderTitle=order_title,
        OrderLines=formatted_order_lines,
        VentilationCode=ventilation_code,
    )

    if set_order_id:
        res[ORDER_BACK_ORDER_ID] = 0

    if about_invoice is not None:
        res["AboutInvoiceNumber"] = about_invoice

    return res
