import re
from typing import TYPE_CHECKING

from flask import jsonify

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

if TYPE_CHECKING:
    from flask.wrappers import Response


def get_customers() -> Response:
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
    return jsonify(formatted)


def get_customer(customer_id: int) -> str:
    customer = CustomerModel.get_one(customer_id)
    return customer.to_front()


def create_customer(json: CustomerFront) -> Response:
    new_customer = CustomerBack.model_validate(json, by_name=True)
    if not new_customer.name and not new_customer.surname and not new_customer.company:
        raise SyncoraError(
            "Missing required fields: name, surname, or company is required.", 1000
        )
    response = ResponseMessage(
        id=CustomerModel.create(new_customer),
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def update_customer(customer_id: int, json: CustomerFront) -> Response:
    json["id"] = customer_id
    updated_customer = CustomerBack.model_validate(json, by_name=True)
    CustomerModel.update(customer_id, updated_customer)
    response = ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def delete_customer(customer_id: int) -> Response:
    CustomerModel.delete(customer_id)
    response = ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def detect_phones(comment: str | None) -> list[str]:
    if comment is None:
        return []

    patterns = [
        r"\+\d{10}",
        r"0\d{8}",
        r"0\d{2}/\d{2} \d{2} \d{2}",
        r"0\d{2}/\d{2},\d{2},\d{2}",
        r"0\d{1}/\d{3} \d{2} \d{2}",
        r"0\d{1}/\d{3},\d{2},\d{2}",
    ]
    phone_numbers = []

    for pattern in patterns:
        phone_numbers.extend(re.findall(pattern, comment))

    cleaned_phone_numbers = []
    for number in phone_numbers:
        cleaned_phone_numbers.append(re.sub(r"[^\d+]", "", number))

    return cleaned_phone_numbers


def detect_mobiles(comment: str | None) -> list[str]:
    if comment is None:
        return []

    patterns = [
        r"\+\d{11}",
        r"0\d{9}",
        r"0\d{3}/\d{2} \d{2} \d{2}",
        r"0\d{3}/\d{2},\d{2},\d{2}",
    ]
    mobile_numbers = []

    for pattern in patterns:
        mobile_numbers.extend(re.findall(pattern, comment))

    cleaned_mobile_numbers = []
    for number in mobile_numbers:
        cleaned_mobile_numbers.append(re.sub(r"[^\d+]", "", number))

    return cleaned_mobile_numbers


def detect_emails(comment: str | None) -> list[str]:
    if comment is None:
        return []

    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, comment)


def is_old_db_comment(comment: str | None) -> bool:
    if comment is None:
        return True

    return not (comment.startswith("##") and comment.endswith("##"))
