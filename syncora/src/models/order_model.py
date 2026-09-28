from typing import TYPE_CHECKING, Any, ClassVar, cast, override

from bson import ObjectId

from classes.syncora_db_class import SyncoraDBClass
from constants.order import (
    ORDER_BACK_DEFAULT_EXTERNAL_ID,
    ORDER_BACK_EXTERNAL_ID,
    ORDER_BACK_ORDER_NUMBER,
    ORDER_BACK_PEPPOL_DELIVERY_STATUS,
)
from constants.peppol import PEPPOL_DELIVERY_STATUS_NOT_SENT
from database.mongodb import get_connection
from dto.back import OrderBack
from utils.generic_error import ItemNotFoundError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from dto.db import OrderDB


class OrderModel[T: OrderBack[Any, Any]](SyncoraDBClass[str, T]):
    database_name: ClassVar[str] = ""
    UsedDTO: type[T] = cast("type[T]", OrderBack)

    @classmethod
    @override
    def get_one(cls, order_id: str) -> T:
        with get_connection() as db:
            order = cast(
                "OrderDB | None",
                db[cls.database_name].find_one({"_id": ObjectId(order_id)}),
            )
        if not order:
            raise ItemNotFoundError(
                cls.database_name, order_id, f"{cls.database_name} database"
            )
        return cls.UsedDTO.from_db(order)

    @classmethod
    @override
    def get(cls, condition: Mapping[str, object] | None = None) -> list[T]:
        with get_connection() as db:
            orders = cast(
                "list[OrderDB]", list(db[cls.database_name].find(condition or {}))
            )
        return [cls.UsedDTO.from_db(order) for order in orders]

    @classmethod
    @override
    def create(cls, order: T) -> str:
        order.externalId = ORDER_BACK_DEFAULT_EXTERNAL_ID
        order.peppolDeliveryStatus = PEPPOL_DELIVERY_STATUS_NOT_SENT
        with get_connection() as db:
            result = db[cls.database_name].insert_one(
                cast("dict[str, object]", order.to_db())
            )
        return str(cast("ObjectId", result.inserted_id))

    @classmethod
    @override
    def update(cls, order_id: str, order: T) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": cast("dict[str, object]", order.to_db())},
            )
        return result.modified_count > 0

    @classmethod
    @override
    def delete(cls, order_id: str) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].delete_one({"_id": ObjectId(order_id)})
        return result.deleted_count > 0

    @classmethod
    @override
    def contains(cls, order_number: str) -> bool:
        with get_connection() as db:
            return (
                db[cls.database_name].find_one({ORDER_BACK_ORDER_NUMBER: order_number})
                is not None
            )

    @classmethod
    def set_peppol_status(cls, external_id: int, peppol_status: int) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {ORDER_BACK_EXTERNAL_ID: external_id},
                {"$set": {ORDER_BACK_PEPPOL_DELIVERY_STATUS: peppol_status}},
            )
        return result.modified_count > 0

    @classmethod
    def set_external_id(cls, order_id: str, external_id: int) -> bool:
        with get_connection() as db:
            result = db[cls.database_name].update_one(
                {"_id": ObjectId(order_id)},
                {"$set": {ORDER_BACK_EXTERNAL_ID: external_id}},
            )
        return result.modified_count > 0
