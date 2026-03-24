import base64
from collections.abc import Callable
from typing import Any

from requests import Response

import constants.order_billit as order_billit

import requests
from dotenv import dotenv_values
from flask import jsonify

from constants.all import *
from constants.order_back import *
from constants.customer import *
from constants.order_billit import BillitPDF
from controllers.billit import get_headers
from models import customers as mcust


def get_orders(filter_query: str = ""):
    url = f"{dotenv_values(".env")["URL"]}/orders{filter_query}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    if response.status_code not in [200, 201]:
        print(response.text)
        return jsonify(ResponseMessage(
            status=RESPONSE_ERROR,
            message=response.json()
        ))

    return response.json()


def get_order(order_id: int):
    url = f"{dotenv_values(".env")["URL"]}/orders/{order_id}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    if response.status_code not in [200, 201]:
        print(response.text)
        return jsonify(ResponseMessage(
            status=RESPONSE_ERROR,
            message=response.json()
        ))
    return response.json()


def delete_order(order_id: int) -> ResponseMessage:
    url = f"{dotenv_values(".env")["URL"]}/orders/{order_id}"
    headers = get_headers()
    response = requests.delete(url, headers=headers)
    if response.content != b'true':
        print(response.text)
    return None if response.content == b'true' else ResponseMessage(status=RESPONSE_ERROR, message=response.text)


def send_peppol(order_id: int):
    url = f"{dotenv_values('.env')['URL']}/orders/commands/send"
    headers = get_headers()
    payload = {
        "OrderIDs": [order_id],
        "SendMethod": "Peppol",
    }
    return requests.post(url, headers=headers, json=payload)


def send_billit(
    order_data: OrderBack,
    pdf_file_name: str,
    *,
    callback: Callable[[Response], Any],
    customer_data: CustomerBack | None = None,
):
    if not customer_data:
        customer_data = mcust.get_customers_dict(
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
                CUSTOMER_DB_SALUTATION,
            ],
            filters={CUSTOMER_DB_ID: order_data['CustomerId']}
        )[order_data['CustomerId']]
    payload = order_billit.order_from_back(order_data, customer_data)

    with open(pdf_file_name, "rb") as pdf_file:
        base64_pdf = base64.b64encode(pdf_file.read())

    payload["OrderPDF"] = BillitPDF(
        FileName=f"bill_{customer_data.last_name}_{customer_data.first_name}_{customer_data.company}_{order_data['OrderNumber']}.pdf",
        FileContent=base64_pdf.decode("utf-8"),
    )

    headers = get_headers()
    url = f"{dotenv_values(".env")['URL']}/orders"
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        callback(response)
        return ResponseMessage(status=RESPONSE_SUCCESS)
    else:
        print(response.text)
        return jsonify(ResponseMessage(
            status=RESPONSE_ERROR,
            message=response.json()
        ))
