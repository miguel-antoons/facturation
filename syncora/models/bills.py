from constants.order_back import *
from constants.order_front import OrderLineFront
from database.mongodb import get_connection
from models.all import ItemNotFoundError
from models.orders import format_order
from bson.objectid import ObjectId


def insert_bill(
    customer_id: int,
    order_number: str,
    order_date: str,
    expiry_date: str,
    delivery_date: str,
    order_title: str,
    order_lines: list[OrderLineFront],
    ventilation_code: str,
) -> str:
    bill_object = format_order(
        customer_id,
        order_number,
        order_date,
        expiry_date,
        delivery_date,
        order_title,
        order_lines,
        ventilation_code,
    )
    bill_object[ORDER_BACK_PEPPOL_DELIVERY_STATUS] = PEPPOL_DELIVERY_STATUS_NOT_SENT
    with get_connection() as db:
        result = db.bills.insert_one(bill_object)
    return str(result.inserted_id)


def update_bill(
    bill_id: str,
    customer_id: int,
    order_number: str,
    order_date: str,
    expiry_date: str,
    delivery_date: str,
    order_title: str,
    order_lines: list[OrderLineFront],
    ventilation_code: str,
) -> bool:
    bill_object = format_order(
        customer_id,
        order_number,
        order_date,
        expiry_date,
        delivery_date,
        order_title,
        order_lines,
        ventilation_code,
        set_order_id=False,
    )
    with get_connection() as db:
        result = db.bills.update_one(
            {"_id": ObjectId(bill_id)},
            {"$set": bill_object}
        )
    return result.modified_count > 0


def set_order_id(bill_id: str, order_id: int) -> bool:
    with get_connection() as db:
        result = db.bills.update_one(
            {"_id": ObjectId(bill_id)},
            {"$set": {ORDER_BACK_ORDER_ID: order_id}}
        )
    return result.modified_count > 0


def set_peppol_status(order_id: int, peppol_status: int) -> bool:
    with get_connection() as db:
        result = db.bills.update_one(
            {ORDER_BACK_ORDER_ID: order_id},
            {"$set": {ORDER_BACK_PEPPOL_DELIVERY_STATUS: peppol_status}}
        )
    return result.modified_count > 0


def get_bill(bill_id: str) -> OrderBack | None:
    with get_connection() as db:
        bill = db.bills.find_one({"_id": ObjectId(bill_id)})
    return bill


def delete_bill(bill_id: str) -> bool:
    with get_connection() as db:
        result = db.bills.delete_one({"_id": ObjectId(bill_id)})
    return result.deleted_count > 0


def get_bills(condition: dict = None) -> list[OrderBack]:
    with get_connection() as db:
        bills = list(db.bills.find(condition or {}))
    return bills


def count_bills(filter_query: dict = None) -> int:
    with get_connection() as db:
        count = db.bills.count_documents(filter_query)
    return count
