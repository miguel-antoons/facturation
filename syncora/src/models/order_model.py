from bson import ObjectId

from constants.order_back import OrderBack, OrderDB, PEPPOL_DELIVERY_STATUS_NOT_SENT, ORDER_BACK_DEFAULT_EXTERNAL_ID, \
    ORDER_BACK_EXTERNAL_ID, ORDER_BACK_PEPPOL_DELIVERY_STATUS, ORDER_BACK_ORDER_NUMBER
from database.mongodb import get_connection
from classes.syncora_db_class import SyncoraDBClass
from utils.generic_error import ItemNotFoundError


class OrderModel(SyncoraDBClass):
    database_name = ""

    @classmethod
    def get_one(cls, order_id: str) -> OrderBack:
        with get_connection() as db:
            order: OrderDB = db[cls.database_name].find_one({"_id": ObjectId(order_id)})
        if not order:
            raise ItemNotFoundError(cls.database_name, order_id, f"{cls.database_name} database")
        return OrderBack.from_db(order)


    @classmethod
    def get(cls, condition: dict | None = None) -> list[OrderBack]:
        with get_connection() as db:
            orders: list[OrderDB] = list(db[cls.database_name].find(condition or {}))
        return [OrderBack.from_db(order) for order in orders]


    @classmethod
    def create(cls, order: OrderBack) -> str:
        order.externalId = ORDER_BACK_DEFAULT_EXTERNAL_ID
        order.peppolDeliveryStatus = PEPPOL_DELIVERY_STATUS_NOT_SENT
        with get_connection() as db:
            result = db[cls.database_name].insert_one(order.to_db())
        return str(result.inserted_id)


    @classmethod
    def update(cls, order_id: str, order: OrderBack) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": order.to_db()}
            )
        return result.modified_count > 0


    @classmethod
    def delete(cls, order_id: str) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].delete_one({"_id": ObjectId(order_id)})
        return result.deleted_count > 0


    @classmethod
    def contains(cls, order_number: str) -> bool:
        with get_connection() as db:
            return db[cls.database_name].find_one({ORDER_BACK_ORDER_NUMBER: order_number}) is not None


    @classmethod
    def set_peppol_status(cls, external_id: int, peppol_status: int) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {ORDER_BACK_EXTERNAL_ID: external_id},
                {"$set": {ORDER_BACK_PEPPOL_DELIVERY_STATUS: peppol_status}}
            )
        return result.modified_count > 0


    @classmethod
    def set_external_id(cls, order_id: str, external_id: int) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {ORDER_BACK_EXTERNAL_ID: external_id}}
            )
        return result.modified_count > 0
