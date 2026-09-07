from typing import Any

from constants.all import RESPONSE_SUCCESS, ResponseMessage
from constants.customer_back import (
    CUSTOMER_DB_CITY,
    CUSTOMER_DB_COMMENT,
    CUSTOMER_DB_COMPANY,
    CUSTOMER_DB_FIRSTNAME,
    CUSTOMER_DB_ID,
    CUSTOMER_DB_NAME,
    CUSTOMER_DB_POSTAL_CODE,
    CUSTOMER_DB_VAT_NUMBER,
    CustomerBack,
    CustomerFront,
)
from models.customers import CustomerModel
from utils.generic_error import SyncoraError


def get_customers() -> list[dict[str, Any]]:
    customers: list[CustomerBack] = CustomerModel.get(
        [
            CUSTOMER_DB_ID,
            CUSTOMER_DB_NAME,
            CUSTOMER_DB_FIRSTNAME,
            CUSTOMER_DB_COMPANY,
            CUSTOMER_DB_COMMENT,
            CUSTOMER_DB_POSTAL_CODE,
            CUSTOMER_DB_CITY,
            CUSTOMER_DB_VAT_NUMBER,
        ]
    )
    formatted = []
    for customer in customers:
        formatted.append(
            customer.model_dump(
                by_alias=False,
                include={
                    "id",
                    "name",
                    "surname",
                    "company",
                    "postal_code",
                    "city",
                    "mobileNumbers",
                    "telephoneNumbers",
                    "hasVAT",
                    "hasEmail",
                },
            )
        )
    return formatted


def get_customer(customer_id: int) -> dict[str, Any]:
    customer = CustomerModel.get_one(customer_id)
    return customer.to_front()


def create_customer(json: CustomerFront) -> ResponseMessage:
    new_customer = CustomerBack.model_validate(json, by_name=True)
    if not new_customer.name and not new_customer.surname and not new_customer.company:
        raise SyncoraError(
            "Missing required fields: name, surname, or company is required.", 1000
        )
    return ResponseMessage(
        id=CustomerModel.create(new_customer),
        status=RESPONSE_SUCCESS,
    )


def update_customer(customer_id: int, json: CustomerFront) -> ResponseMessage:
    json["id"] = customer_id
    updated_customer = CustomerBack.model_validate(json, by_name=True)
    if not CustomerModel.contains(customer_id):
        raise SyncoraError("Customer not found.", 1001)
    CustomerModel.update(customer_id, updated_customer)
    return ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )


def delete_customer(customer_id: int) -> ResponseMessage:
    CustomerModel.delete(customer_id)
    return ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )
