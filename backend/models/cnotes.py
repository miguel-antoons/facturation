from constants.order_back import *
from constants.order_front import OrderLineFront
from database.mongodb import get_connection
from models.orders import format_order
from bson.objectid import ObjectId


def insert_cnote(
    customer_id: int,
    order_number: str,
    order_date: str,
    expiry_date: str,
    delivery_date: str,
    order_title: str,
    order_lines: list[OrderLineFront],
    ventilation_code: str,
    about_invoice: str,
) -> str:
    cnote_object = format_order(
        customer_id,
        order_number,
        order_date,
        expiry_date,
        delivery_date,
        order_title,
        order_lines,
        ventilation_code,
        about_invoice=about_invoice,
    )
    cnote_object[ORDER_BACK_PEPPOL_DELIVERY_STATUS] = PEPPOL_DELIVERY_STATUS_NOT_SENT
    with get_connection() as db:
        result = db.cnotes.insert_one(cnote_object)
    return str(result.inserted_id)


def update_cnote(
    cnote_id: str,
    customer_id: int,
    order_number: str,
    order_date: str,
    expiry_date: str,
    delivery_date: str,
    order_title: str,
    order_lines: list[OrderLineFront],
    ventilation_code: str,
    about_invoice: str,
) -> bool:
    cnote_object = format_order(
        customer_id,
        order_number,
        order_date,
        expiry_date,
        delivery_date,
        order_title,
        order_lines,
        ventilation_code,
        about_invoice=about_invoice,
    )
    with get_connection() as db:
        result = db.cnotes.update_one(
            {"_id": ObjectId(cnote_id)},
            {"$set": cnote_object}
        )
    return result.modified_count > 0


def set_order_id(cnote_id: str, order_id: int) -> bool:
    with get_connection() as db:
        result = db.cnotes.update_one(
            {"_id": ObjectId(cnote_id)},
            {"$set": {ORDER_BACK_ORDER_ID: order_id}}
        )
    return result.modified_count > 0


def set_peppol_status(order_id: int, peppol_status: int) -> bool:
    with get_connection() as db:
        result = db.cnotes.update_one(
            {ORDER_BACK_ORDER_ID: order_id},
            {"$set": {ORDER_BACK_PEPPOL_DELIVERY_STATUS: peppol_status}}
        )
    return result.modified_count > 0


def get_cnote(cnote_id: str) -> OrderBack | None:
    with get_connection() as db:
        cnote = db.cnotes.find_one({"_id": ObjectId(cnote_id)})
    return cnote


def delete_cnote(cnote_id: str) -> bool:
    with get_connection() as db:
        result = db.cnotes.delete_one({"_id": ObjectId(cnote_id)})
    return result.deleted_count > 0


def get_cnotes(condition: dict = None) -> list[OrderBack]:
    with get_connection() as db:
        cnotes = list(db.cnotes.find(condition or {}))
    return cnotes


def count_bills(filter_query: dict = None) -> int:
    with get_connection() as db:
        count = db.cnotes.count_documents(filter_query)
    return count
