from flask import jsonify
import requests
from dotenv import dotenv_values

from controllers.orders import get_headers, format_client, send_peppol, get_orders, get_order, delete_order


def get_bills():
    return get_orders("?$filter=OrderType eq 'Invoice' and OrderDirection eq 'Income'")


def create_bill(json, order_id=0):
    client_payload = format_client(json.get('customerId'))
    if 'status' in client_payload and client_payload['status'] == 'failed':
        return jsonify(client_payload)

    order_lines = json.get('orderLines', [])
    order_lines_payload = []
    for line in order_lines:
        order_lines_payload.append({
            "Description": line.get('description'),
            "Quantity": line.get('quantity'),
            "UnitPriceExcl": line.get('unitPriceExcl'),
            "Unit": line.get('unit'),
            "VATPercentage": line.get('VATPercentage'),
        })

    payload = {
        "Customer": client_payload,
        "OrderType": "Invoice",
        "OrderDirection": "Income",
        "OrderNumber": json.get('orderNumber'),
        "OrderDate": json.get('orderDate'),
        "ExpiryDate": json.get('expiryDate'),
        "DeliveryDate": json.get('deliveryDate'),
        "OrderTitle": json.get('orderTitle'),
        "OrderLines": order_lines_payload,
        "VentilationCode": json.get('ventilationCode', ''),
    }
    if order_id != 0:
        payload["OrderID"] = order_id

    headers = get_headers()
    url = f"{dotenv_values(".env")['URL']}/orders"
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        return jsonify({"status": "success", "id": response.json()})
    else:
        print(response.text)
        return jsonify({
            "status": "failed",
            "message": response.json()
        })


def get_bill(bill_id):
    return get_order(bill_id)


def update_bill(bill_id, json):
    return create_bill(json, order_id=bill_id)


def delete_bill(bill_id):
    return delete_order(bill_id)


def send_bill_peppol(bill_id):
    return send_peppol(bill_id)
