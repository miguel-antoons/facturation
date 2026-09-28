from typing import TYPE_CHECKING, Any, override

from classes.syncora_db_class import SyncoraDBClass
from constants.customer_fields import (
    CUSTOMER_DB_ADDRESS,
    CUSTOMER_DB_ARCHITECT_NAME,
    CUSTOMER_DB_CITY,
    CUSTOMER_DB_COMMENT,
    CUSTOMER_DB_COMPANY,
    CUSTOMER_DB_FIRSTNAME,
    CUSTOMER_DB_ID,
    CUSTOMER_DB_LANGUAGE,
    CUSTOMER_DB_NAME,
    CUSTOMER_DB_POSTAL_CODE,
    CUSTOMER_DB_SALUTATION,
    CUSTOMER_DB_VAT_NUMBER,
)
from database import access
from dto.back import CustomerBack

if TYPE_CHECKING:
    from collections.abc import Mapping


class CustomerModel(SyncoraDBClass[int, CustomerBack]):

    @staticmethod
    def _customer_list(fields: list[str], results: list[Any]) -> list[CustomerBack]:
        customers = []
        for customer in results:
            customers.append(CustomerBack.from_db((fields, customer)))

        return customers

    @staticmethod
    def _customer_dict(
        fields: list[str], results: list[Any]
    ) -> dict[int, CustomerBack]:
        customer_dict = {}
        for customer in results:
            customer_class = CustomerBack.from_db((fields, customer))
            customer_dict[customer_class.id] = customer_class

        return customer_dict

    @staticmethod
    def _get_last_id() -> int:
        query = f"SELECT MAX({CUSTOMER_DB_ID}) FROM Client"  # noqa: S608

        result = access.get_connection().execute_query(query, fetch_one=True)

        return result[0] if result and result[0] is not None else 0

    @classmethod
    @override
    def get_one(cls, customer_id: int) -> CustomerBack:
        return CustomerModel.get(
            [
                CUSTOMER_DB_ID,
                CUSTOMER_DB_NAME,
                CUSTOMER_DB_FIRSTNAME,
                CUSTOMER_DB_COMPANY,
                CUSTOMER_DB_COMMENT,
                CUSTOMER_DB_ADDRESS,
                CUSTOMER_DB_POSTAL_CODE,
                CUSTOMER_DB_CITY,
                CUSTOMER_DB_VAT_NUMBER,
                CUSTOMER_DB_LANGUAGE,
                CUSTOMER_DB_ARCHITECT_NAME,
                CUSTOMER_DB_SALUTATION,
            ],
            filters={CUSTOMER_DB_ID: customer_id},
        )[0]

    @classmethod
    @override
    def get(
        cls,
        fields: list[str],
        *,
        filters: Mapping[str, object] | None = None,
        by_id: bool = False,
    ) -> list[CustomerBack] | dict[int, CustomerBack]:
        fields = [CUSTOMER_DB_ID] + fields if CUSTOMER_DB_ID not in fields else fields
        formatted_fields = [f"`{field}`" for field in fields]
        query = f'SELECT {", ".join(formatted_fields)} FROM Client'  # noqa: S608
        if filters:
            filter_clauses = [f"{key} = ?" for key in filters]
            query += " WHERE " + " AND ".join(filter_clauses)

        results = access.get_connection().execute_query(
            query, tuple(filters.values()) if filters else ()
        )

        if by_id:
            return CustomerModel._customer_dict(fields, results)
        return CustomerModel._customer_list(fields, results)

    @classmethod
    @override
    def create(cls, data: CustomerBack) -> int:
        fields, values = data.to_db()
        fields = ", ".join(fields)
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO Client ({fields}) VALUES ({placeholders})"  # noqa: S608

        access.get_connection().execute_query(query, tuple(values))

        return CustomerModel._get_last_id()

    @classmethod
    @override
    def update(cls, customer_id: int, data: CustomerBack) -> None:
        fields, values = data.to_db()
        set_clauses = ", ".join([f"{field} = ?" for field in fields])
        query = (
            f"UPDATE Client SET {set_clauses} WHERE {CUSTOMER_DB_ID} = ?"  # noqa: S608
        )

        access.get_connection().execute_query(query, tuple(values) + (customer_id,))

    @classmethod
    @override
    def contains(cls, customer_id: int) -> bool:
        query = f"SELECT 1 FROM Client WHERE {CUSTOMER_DB_ID} = ?"  # noqa: S608

        result = access.get_connection().execute_query(
            query, (customer_id,), fetch_one=True
        )

        return result is not None and len(result) > 0

    @classmethod
    @override
    def delete(cls, customer_id: int) -> None:
        query = f"DELETE FROM Client WHERE {CUSTOMER_DB_ID} = ?"  # noqa: S608
        access.get_connection().execute_query(query, (customer_id,))
