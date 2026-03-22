import threading

from flask import jsonify, Response

from constants.all import *
from constants.order_back import ORDER_BACK_PEPPOL_DELIVERY_STATUS, PEPPOL_DELIVERY_STATUS_PENDING, \
    PEPPOL_DELIVERY_STATUS_UNKNOWN, ORDER_BACK_ORDER_ID, OrderBack, PEPPOL_DELIVERY_STATUS_SENT
from constants.order_front import convert_order_back_to_front, OrderFront, OrderFrontShort
from constants.customer import *
from controllers.billit import order_locked, bill_undeletable
from controllers.orders import send_peppol, send_billit
import controllers.bill_gen as pdf
import models.bills as model
import models.customers as mcust
from utils.peppol_poller import PeppolStatusPoller
import controllers.orders as order


def create_bill(json: OrderFront, db_id: str = "") -> Response:
    order_ids_with_same_number = {str(bill['_id']) for bill in model.get_bills(condition={"OrderNumber": json.get('orderNumber')})}
    # Check for duplicate order numbers
    if db_id not in order_ids_with_same_number and len(order_ids_with_same_number) > 0:
        return jsonify(ResponseMessage(
            status=RESPONSE_ERROR,
            message=f"Une facture avec le numéro {json.get('orderNumber')} existe déjà. Veuillez choisir un numéro de facture unique.",
        ))

    if not db_id:
        db_id = model.insert_bill(
            customer_id=json.get('customerId'),
            order_number=json.get('orderNumber'),
            order_date=json.get('orderDate'),
            expiry_date=json.get('expiryDate'),
            delivery_date=json.get('deliveryDate'),
            order_title=json.get('orderTitle'),
            order_lines=json.get('orderLines'),
            ventilation_code=json.get('ventilationCode', ''),
        )
    else:
        order_data = model.get_bill(db_id)
        if order_locked(order_data):
            return jsonify(ResponseMessage(
                status=RESPONSE_WARNING,
                message=f"Facture avec l'ID {order_data['OrderNumber']} a déjà été envoyée à Billit et est verrouillée.",
            ))
        _ = model.update_bill(
            bill_id=db_id,
            customer_id=json.get('customerId'),
            order_number=json.get('orderNumber'),
            order_date=json.get('orderDate'),
            expiry_date=json.get('expiryDate'),
            delivery_date=json.get('deliveryDate'),
            order_title=json.get('orderTitle'),
            order_lines=json.get('orderLines'),
            ventilation_code=json.get('ventilationCode', ''),
        )

    return jsonify(ResponseMessage(
        status=RESPONSE_SUCCESS,
        id=db_id,
    ))


def get_bill(bill_id: str) -> Response:
    order_back = model.get_bill(bill_id)
    if (
        ORDER_BACK_PEPPOL_DELIVERY_STATUS in order_back
        and (
            order_back[ORDER_BACK_PEPPOL_DELIVERY_STATUS] == PEPPOL_DELIVERY_STATUS_PENDING
            or order_back[ORDER_BACK_PEPPOL_DELIVERY_STATUS] == PEPPOL_DELIVERY_STATUS_UNKNOWN
        )
    ):
        PeppolStatusPoller(model.set_peppol_status)(order_back[ORDER_BACK_ORDER_ID])

    return jsonify(convert_order_back_to_front(order_back))


def get_bills() -> Response:
    bills = model.get_bills()
    customers = mcust.get_customers_dict(
        [
            CUSTOMER_DB_NAME,
            CUSTOMER_DB_FIRSTNAME,
            CUSTOMER_DB_COMPANY
        ]
    )
    bills_front = []
    for bill in bills:
        cust_id = bill.get('CustomerId')
        customer_name = f"{customers[cust_id][CUSTOMER_DB_NAME] or ""} {customers[cust_id][CUSTOMER_DB_FIRSTNAME] or ""}".strip()
        customer_name += ", " if customer_name and customers[cust_id].get(CUSTOMER_DB_COMPANY) else ""
        customer_name += f"{customers[cust_id].get(CUSTOMER_DB_COMPANY)}" if customers[cust_id].get(CUSTOMER_DB_COMPANY) else ""
        bills_front.append(OrderFrontShort(
            orderId=str(bill.get('_id')),
            customerName=customer_name,
            orderNumber=bill.get('OrderNumber'),
            orderDate=bill.get('OrderDate'),
            orderTitle=bill.get('OrderTitle')
        ))
    return jsonify(bills_front)


def update_bill(bill_id: str, json: OrderFront) -> Response:
    return create_bill(json, db_id=bill_id)


def delete_bill(bill_id: str) -> Response:
    order_data = model.get_bill(bill_id)
    if bill_undeletable(order_data):
        return jsonify(ResponseMessage(
            status=RESPONSE_WARNING,
            message=f"Facture avec l'ID {bill_id} a déjà été envoyée à Peppol et ne peut pas être supprimée.",
        ))
    if order_data[ORDER_BACK_ORDER_ID] and (res := order.delete_order(order_data[ORDER_BACK_ORDER_ID])):
        return jsonify(res)
    bill_deleted = model.delete_bill(bill_id)
    if not bill_deleted:
        print("ERROR: Bill not deleted from local DB")
    return jsonify(ResponseMessage(status=RESPONSE_SUCCESS if bill_deleted else RESPONSE_ERROR))


def pre_peppol_checks(order_data: OrderBack) -> ResponseMessage | None:
    message = None
    if not order_data[ORDER_BACK_ORDER_ID]:
        message = f"Facture avec l'ID {order_data["OrderNumber"]} n'est pas encore enregistré sur Billit. Veuillez d'abord enregistrer la facture avant de l'envoyer via Peppol."
    elif (
        order_data["PeppolDeliveryStatus"] == PEPPOL_DELIVERY_STATUS_PENDING
        or order_data["PeppolDeliveryStatus"] == PEPPOL_DELIVERY_STATUS_SENT
    ):
        message=f"Facture avec l'ID {order_data['OrderNumber']} a déjà été envoyée à Peppol. Impossible de la ré-envoyer."
    elif (
        not mcust.get_customers_dict(
            [CUSTOMER_DB_VAT_NUMBER],
            filters={CUSTOMER_DB_ID: order_data['CustomerId']}
        )[order_data['CustomerId']].get(CUSTOMER_DB_VAT_NUMBER)
    ):
        message = f"Le client associé à la facture avec l'ID {order_data['OrderNumber']} n'a pas de numéro de TVA. Veuillez ajouter un numéro de TVA au client avant d'envoyer la facture à Peppol."

    return ResponseMessage(
        status=RESPONSE_WARNING,
        message=message,
    ) if message else None


def send_bill_peppol(bill_id: str) -> Response:
    order_data: OrderBack = model.get_bill(bill_id)
    if res := pre_peppol_checks(order_data):
        return jsonify(res)
    response = send_peppol(order_data[ORDER_BACK_ORDER_ID])
    if response.status_code in [200, 201]:
        model.set_peppol_status(order_data[ORDER_BACK_ORDER_ID], PEPPOL_DELIVERY_STATUS_UNKNOWN)
        PeppolStatusPoller(model.set_peppol_status)(order_data[ORDER_BACK_ORDER_ID])
        return jsonify(ResponseMessage(status=RESPONSE_SUCCESS))
    else:
        print(response.text)
        return jsonify(ResponseMessage(
            status=RESPONSE_ERROR,
            message=response.json()
        ))


def pre_billit_checks(order_data: OrderBack) -> ResponseMessage | None:
    message = None
    if order_locked(order_data):
        message = f"Facture avec l'ID {order_data['OrderNumber']} a déjà été envoyée à Billit et est verrouillée."
    elif not order_data["CustomerId"]:
        message = f"Facture avec l'ID {order_data['OrderNumber']} n'a pas de client associé. Veuillez associer un client avant de l'envoyer à Billit."
    elif not order_data["OrderTitle"]:
        message = f"Facture avec l'ID {order_data['OrderNumber']} n'a pas de titre. Veuillez ajouter un titre avant de l'envoyer à Billit."
    elif not order_data["OrderNumber"]:
        message = f"Facture avec l'ID {order_data['_id']} n'a pas de numéro de facture. Veuillez ajouter un numéro de facture avant de l'envoyer à Billit."
    elif not order_data["VentilationCode"]:
        message = f"Facture avec l'ID {order_data['OrderNumber']} n'a pas de code de taux de TVA valide. Veuillez ajouter un taux de TVA valide avant de l'envoyer à Billit."
    elif not len(order_data["OrderLines"]):
        message = f"Facture avec l'ID {order_data['OrderNumber']} n'a pas de lignes de facture. Veuillez ajouter au moins une ligne de commande avant de l'envoyer à Billit."
    elif len(order_data["OrderLines"]):
        for line in order_data["OrderLines"]:
            if not line.get("Description"):
                message = f"Facture avec l'ID {order_data['OrderNumber']} a une ligne de commande sans description. Veuillez ajouter une description à toutes les lignes de commande avant de l'envoyer à Billit."
                break
            elif not line.get("Quantity") or line.get("Quantity") <= 0:
                message = f"Facture avec l'ID {order_data['OrderNumber']} a une ligne de commande avec une quantité invalide. Veuillez ajouter une quantité valide à toutes les lignes de commande avant de l'envoyer à Billit."
                break
            elif not line.get("UnitPriceExcl") or line.get("UnitPriceExcl") < 0:
                message = f"Facture avec l'ID {order_data['OrderNumber']} a une ligne de commande avec un prix unitaire hors taxe invalide. Veuillez ajouter un prix unitaire hors taxe valide à toutes les lignes de commande avant de l'envoyer à Billit."
                break

    return ResponseMessage(
        status=RESPONSE_WARNING,
        message=message,
    ) if message else None


def send_bill_billit(bill_id: str) -> Response:
    order_data = model.get_bill(bill_id)

    if res := pre_billit_checks(order_data):
        return jsonify(res)

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

    filename = pdf.create_bill(order_data, customer_data)
    return send_billit(
        order_data,
        filename,
        callback=lambda response: model.set_order_id(bill_id, int(response.json())),
        customer_data=customer_data
    )
