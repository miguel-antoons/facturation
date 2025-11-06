import requests
from dotenv import dotenv_values
from flask import jsonify

from models import customers as mcust
from controllers import customers as cctrl


def get_headers():
    return {
        "accept": "application/json",
        "apiKey": dotenv_values(".env")["API_SECRET"],
        "partyID": dotenv_values(".env")["PARTY_ID"],
        "contextPartyID": dotenv_values(".env")["PARTY_ID"]
    }


def get_orders(filter_query=""):
    url = f"{dotenv_values(".env")["URL"]}/orders{filter_query}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    if response.status_code not in [200, 201]:
        print(response.text)
        return jsonify({
            "status": "failed",
            "message": response.json()
        })

    return response.json()


def get_order(order_id):
    url = f"{dotenv_values(".env")["URL"]}/orders/{order_id}"
    headers = get_headers()
    response = requests.get(url, headers=headers)
    if response.status_code not in [200, 201]:
        print(response.text)
        return jsonify({
            "status": "failed",
            "message": response.json()
        })
    return response.json()


def delete_order(order_id):
    url = f"{dotenv_values(".env")["URL"]}/orders/{order_id}"
    headers = get_headers()
    response = requests.delete(url, headers=headers)
    if response.content != b'true':
        print(response.text)
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
        print("Invalid address format for customer ID:", customer_id)
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


def send_peppol(bill_id):
    url = f"{dotenv_values('.env')['URL']}/orders/commands/send"
    headers = get_headers()
    payload = {
        "OrderIDs": [bill_id],
        "SendMethod": "Peppol",
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        return jsonify({"status": "success"})
    else:
        print(response.text)
        return jsonify({
            "status": "failed",
            "message": response.json()
        })