from flask import jsonify
import requests
from dotenv import dotenv_values

from models import customers as mcust
from controllers import customers as cctrl


def get_bills():
    url = f"{dotenv_values(".env")["URL"]}/orders"
    headers = get_headers()
    response = requests.get(url, headers=headers)

    return response.json()


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
                .get('errors', 'Erreur lors de la création de la facture.')[0]
                .get('Description', 'Erreur lors de la création de la facture.')
        })


def get_bill(bill_id):
    url = f"{dotenv_values(".env")["URL"]}/orders/{bill_id}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    return response.json()


def update_bill(bill_id, json):
    return create_bill(json, order_id=bill_id)


def delete_bill(bill_id):
    url = f"{dotenv_values(".env")["URL"]}/orders/{bill_id}"
    headers = get_headers()
    response = requests.delete(url, headers=headers)
    return jsonify({"status": "deleted" if response.content == b'true' else "failed"})


def format_client(customer_id):
    customer = mcust.get_customers(
        [
            'Numero',
            'Nom',
            'Prenom',
            'Societe',
            'Commentaire',
            'Adresse',
            'Codepostal',
            'Localite',
            'TVA',
            'Langue',
        ],
        filters={'Numero': customer_id}
    )

    address = customer[0][5].split(',')
    if len(address) > 1:
        street = address[0].strip()
        street_number = address[1].strip()
        # box_index = -1
        # for index, ch in enumerate(street_number):
        #     if ch.isalpha():
        #         box_index = index
        #         break
        # box = ""
        # if box_index != -1:
        #     street_number, box = street_number[:box_index].strip(), street_number[box_index:].strip()
        #     if box.lower().startswith('bte'):
        #         box = box[3:].strip()
        #     elif box.lower().startswith('boite'):
        #         box = box[5:].strip()
    else:
        return {
            "status": "failed",
            "message": "Format d'adresse incorrect. L'adresse devrait avoir le format 'Rue , Numéro'."
        }

    customer_emails = cctrl.detect_emails(customer[0][4])
    phones = cctrl.detect_phones(customer[0][4])
    mobiles = cctrl.detect_mobiles(customer[0][4])
    return {
        "Nr": customer[0][0],
        "Name": customer[0][3],
        "VATNumber": customer[0][8],
        "Zipcode": customer[0][6],
        "City": customer[0][7],
        "Street": street,
        "StreetNumber": street_number,
        # "Box": box if 'box' in locals() else "",
        "CountryCode": "BE",
        "ContactFirstName": customer[0][2],
        "ContactLastName": customer[0][1],
        "Language": customer[0][9].upper(),
        "Email": customer_emails[0] if len(customer_emails) > 0 else "",
        "Phone": phones[0] if len(phones) > 0 else "",
        "Mobile": mobiles[0] if len(mobiles) > 0 else "",
        "PartyType": "Customer",
        "Addresses": [
            {
                "AddressType": "InvoiceAddress",
                "Street": street,
                "StreetNumber": street_number,
                "City": customer[0][7],
                "Zipcode": customer[0][6],
                "CountryCode": "BE"
            }
        ],
    }


def get_headers():
    return {
        "accept": "application/json",
        "apiKey": dotenv_values(".env")["API_SECRET"],
        "partyID": dotenv_values(".env")["PARTY_ID"],
        "contextPartyID": dotenv_values(".env")["PARTY_ID"]
    }
