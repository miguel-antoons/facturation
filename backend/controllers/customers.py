from flask import jsonify

from models import customers as model
import re
from constants.customer import *
from constants.all import *


def get_customers():
    customers = model.get_customers([
        CUSTOMER_DB_ID,
        CUSTOMER_DB_NAME,
        CUSTOMER_DB_FIRSTNAME,
        CUSTOMER_DB_COMPANY,
        CUSTOMER_DB_COMMENT,
        CUSTOMER_DB_POSTAL_CODE,
        CUSTOMER_DB_CITY,
        CUSTOMER_DB_VAT_NUMBER,
    ])
    formatted = []
    for customer in customers:
        formatted.append(CustomerFront(
            id=customer[0],
            name=customer[1],
            surname=customer[2],
            company=customer[3],
            phones=detect_phones(customer[4]) + detect_mobiles(customer[4]),
            hasEmail=len(detect_emails(customer[4])) > 0,
            hasVAT=customer[7] is not None and customer[7] != '',
            postal_code=customer[5],
            city=customer[6],
        ))
    return jsonify(formatted)


def get_customer(customer_id: int):
    customer = model.get_customers(
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
        filters={CUSTOMER_DB_ID: customer_id}
    )
    formatted = CustomerFront(
        id=customer[0][0],
        name=customer[0][1],
        surname=customer[0][2],
        company=customer[0][3],
        comment=customer[0][4],
        street=model.get_customer_street(customer[0][5]),
        number=model.get_customer_street_number(customer[0][5]),
        postal_code=customer[0][6],
        city=customer[0][7],
        vat_number=customer[0][8],
        language=customer[0][9],
        architect_name=customer[0][10],
        salutation=customer[0][11],
    )
    return jsonify(formatted)


def create_customer(json: CustomerFront):
    new_customer = CustomerBack(
        Numero=model.get_last_customer_id() + 1,
        Nom=json.get('name'),
        Prenom=json.get('surname'),
        Societe=json.get('company'),
        Commentaire=json.get('comment'),
        Adresse=f"{json.get('street').strip()} , {json.get('number').strip()}",
        Codepostal=json.get('postal_code'),
        Localite=json.get('city'),
        TVA=json.get('vat_number'),
        Langue=json.get('language'),
        NomArchitecte=json.get('architect_name'),
        Titre=json.get('salutation'),
    )
    response = ResponseMessage(
        id=model.create_customer(new_customer),
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def update_customer(customer_id: int, json: CustomerFront):
    updated_customer = CustomerBack(
        Nom=json.get('name'),
        Prenom=json.get('surname'),
        Societe=json.get('company'),
        Commentaire=json.get('comment'),
        Adresse=f"{json.get('street').strip()} , {json.get('number').strip()}",
        Codepostal=json.get('postal_code'),
        Localite=json.get('city'),
        TVA=json.get('vat_number'),
        Langue=json.get('language'),
        NomArchitecte=json.get('architect_name'),
        Titre=json.get('salutation'),
    )
    model.update_customer(customer_id, updated_customer)
    response = ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def delete_customer(customer_id: int):
    model.delete_customer(customer_id)
    response = ResponseMessage(
        id=customer_id,
        status=RESPONSE_SUCCESS,
    )
    return jsonify(response)


def detect_phones(comment: str | None) -> list[str]:
    if comment is None:
        return []

    patterns = [
        r'\+\d{10}',
        r'0\d{8}',
        r'0\d{2}/\d{2} \d{2} \d{2}',
        r'0\d{2}/\d{2},\d{2},\d{2}',
        r'0\d{1}/\d{3} \d{2} \d{2}',
        r'0\d{1}/\d{3},\d{2},\d{2}',
    ]
    phone_numbers = []

    for pattern in patterns:
        phone_numbers.extend(re.findall(pattern, comment))

    cleaned_phone_numbers = []
    for number in phone_numbers:
        cleaned_phone_numbers.append(re.sub(r'[^\d+]', '', number))

    return cleaned_phone_numbers


def detect_mobiles(comment: str | None) -> list[str]:
    if comment is None:
        return []

    patterns = [
        r'\+\d{11}',
        r'0\d{9}',
        r'0\d{3}/\d{2} \d{2} \d{2}',
        r'0\d{3}/\d{2},\d{2},\d{2}',
    ]
    mobile_numbers = []

    for pattern in patterns:
        mobile_numbers.extend(re.findall(pattern, comment))

    cleaned_mobile_numbers = []
    for number in mobile_numbers:
        cleaned_mobile_numbers.append(re.sub(r'[^\d+]', '', number))

    return cleaned_mobile_numbers


def detect_emails(comment: str | None) -> list[str]:
    if comment is None:
        return []

    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, comment)


def is_old_db_comment(comment: str | None) -> bool:
    if comment is None:
        return True

    return not (comment.startswith('##') and comment.endswith('##'))
