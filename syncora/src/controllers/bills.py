import controllers.bill_gen as pdf
from constants.all import (
    RESPONSE_ERROR,
    RESPONSE_SUCCESS,
    RESPONSE_WARNING,
    ResponseMessage,
)
from constants.customer_back import (
    CUSTOMER_DB_COMPANY,
    CUSTOMER_DB_FIRSTNAME,
    CUSTOMER_DB_NAME,
)
from constants.order_back import (
    PEPPOL_DELIVERY_STATUS_PENDING,
    PEPPOL_DELIVERY_STATUS_SENT,
    PEPPOL_DELIVERY_STATUS_UNKNOWN,
    OrderBack,
)
from constants.order_front import OrderFront, OrderFrontShort
from controllers import billit
from controllers.billit import send_billit, send_peppol
from models.bills import BillModel
from models.customers import CustomerModel
from utils.peppol_poller import PeppolStatusPoller


def create_bill(json: OrderFront, db_id: str = "") -> ResponseMessage:
    bill = OrderBack.model_validate(json, by_name=True)
    existing = BillModel.get_one(db_id) if db_id else None

    # Reject a duplicate order number, unless it belongs to the bill being edited.
    if BillModel.contains(bill.orderNumber) and (
        existing is None or existing.orderNumber != bill.orderNumber
    ):
        return ResponseMessage(
            status=RESPONSE_ERROR,
            message=(
                f"Une facture avec le numéro {json.get('orderNumber')} "
                "existe déjà. Veuillez choisir un numéro de facture unique."
            ),
        )

    if not db_id:
        db_id = BillModel.create(bill)
    else:
        if existing.locked:
            return ResponseMessage(
                status=RESPONSE_WARNING,
                message=(
                    f"Facture avec l'ID {existing.orderNumber} a déjà été "
                    "envoyée à Billit et est verrouillée."
                ),
            )
        _ = BillModel.update(db_id, bill)

    return ResponseMessage(
        status=RESPONSE_SUCCESS,
        id=db_id,
    )


def get_bill(bill_id: str) -> dict:
    order_back = BillModel.get_one(bill_id)
    if (
        order_back.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_PENDING
        or order_back.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_UNKNOWN
    ):
        PeppolStatusPoller(BillModel.set_peppol_status)(order_back.externalId)
    return order_back.to_front()


def get_bills() -> list[OrderFrontShort]:
    bills = BillModel.get()
    customers = CustomerModel.get(
        [CUSTOMER_DB_NAME, CUSTOMER_DB_FIRSTNAME, CUSTOMER_DB_COMPANY], by_id=True
    )
    bills_front = []
    for bill in bills:
        cust_id = bill.customerId
        name = customers[cust_id].name or ""
        surname = customers[cust_id].surname or ""
        customer_name = f"{name} {surname}".strip()
        customer_name += ", " if customer_name and customers[cust_id].company else ""
        customer_name += (
            f"{customers[cust_id].company}" if customers[cust_id].company else ""
        )
        bills_front.append(
            OrderFrontShort(
                orderId=str(bill.orderId),
                customerName=customer_name,
                orderNumber=bill.orderNumber,
                orderDate=bill.orderDate,
                orderTitle=bill.orderTitle,
            )
        )
    return bills_front


def update_bill(bill_id: str, json: OrderFront) -> ResponseMessage:
    return create_bill(json, db_id=bill_id)


def delete_bill(bill_id: str) -> ResponseMessage:
    order_data = BillModel.get_one(bill_id)
    if order_data.undeletable:
        return ResponseMessage(
            status=RESPONSE_WARNING,
            message=(
                f"Facture avec l'ID {bill_id} a déjà été envoyée à Peppol "
                "et ne peut pas être supprimée."
            ),
        )
    if order_data.externalId and (res := billit.delete_order(order_data.externalId)):
        return res
    bill_deleted = BillModel.delete(bill_id)
    if not bill_deleted:
        print("ERROR: Bill not deleted from local DB")
    return ResponseMessage(status=RESPONSE_SUCCESS if bill_deleted else RESPONSE_ERROR)


def pre_peppol_checks(order_data: OrderBack) -> ResponseMessage | None:
    message = None
    if not order_data.externalId:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'est pas encore "
            "enregistré sur Billit. Veuillez d'abord enregistrer la facture "
            "avant de l'envoyer via Peppol."
        )
    elif (
        order_data.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_PENDING
        or order_data.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_SENT
    ):
        message = (
            f"Facture avec l'ID {order_data.orderNumber} a déjà été envoyée "
            "à Peppol. Impossible de la ré-envoyer."
        )
    elif not CustomerModel.get_one(order_data.customerId).vat_number:
        message = (
            f"Le client associé à la facture avec l'ID {order_data.orderNumber} "
            "n'a pas de numéro de TVA. Veuillez ajouter un numéro de TVA au "
            "client avant d'envoyer la facture à Peppol."
        )

    return (
        ResponseMessage(
            status=RESPONSE_WARNING,
            message=message,
        )
        if message
        else None
    )


def send_bill_peppol(bill_id: str) -> ResponseMessage:
    order_data: OrderBack = BillModel.get_one(bill_id)
    if res := pre_peppol_checks(order_data):
        return res
    response = send_peppol(order_data.externalId)
    if response.status_code in [200, 201]:
        BillModel.set_peppol_status(
            order_data.externalId, PEPPOL_DELIVERY_STATUS_UNKNOWN
        )
        PeppolStatusPoller(BillModel.set_peppol_status)(order_data.externalId)
        return ResponseMessage(status=RESPONSE_SUCCESS)
    print(response.text)
    return ResponseMessage(status=RESPONSE_ERROR, message=response.json())


def pre_billit_checks(order_data: OrderBack) -> ResponseMessage | None:  # noqa: C901
    message = None
    if order_data.locked:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} a déjà été envoyée "
            "à Billit et est verrouillée."
        )
    elif not order_data.orderNumber:
        message = (
            f"Facture avec l'ID {order_data.orderId} n'a pas de numéro de "
            "facture. Veuillez ajouter un numéro de facture avant de l'envoyer "
            "à Billit."
        )
    elif not order_data.customerId:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'a pas de client "
            "associé. Veuillez associer un client avant de l'envoyer à Billit."
        )
    elif not order_data.orderTitle:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'a pas de titre. "
            "Veuillez ajouter un titre avant de l'envoyer à Billit."
        )
    elif not order_data.ventilationCode:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'a pas de code de "
            "taux de TVA valide. Veuillez ajouter un taux de TVA valide avant "
            "de l'envoyer à Billit."
        )
    elif not len(order_data.orderLines):
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'a pas de lignes "
            "de facture. Veuillez ajouter au moins une ligne de commande "
            "avant de l'envoyer à Billit."
        )
    elif len(order_data.orderLines):
        for line in order_data.orderLines:
            if not line.description:
                message = (
                    f"Facture avec l'ID {order_data.orderNumber} a une ligne de "
                    "commande sans description. Veuillez ajouter une description "
                    "à toutes les lignes de commande avant de l'envoyer à Billit."
                )
                break
            if not line.quantity or line.quantity <= 0:
                message = (
                    f"Facture avec l'ID {order_data.orderNumber} a une ligne de "
                    "commande avec une quantité invalide. Veuillez ajouter une "
                    "quantité valide à toutes les lignes de commande avant de "
                    "l'envoyer à Billit."
                )
                break
            if not line.unitPriceExcl or line.unitPriceExcl < 0:
                message = (
                    f"Facture avec l'ID {order_data.orderNumber} a une ligne de "
                    "commande avec un prix unitaire hors taxe invalide. "
                    "Veuillez ajouter un prix unitaire hors taxe valide à toutes "
                    "les lignes de commande avant de l'envoyer à Billit."
                )
                break

    return (
        ResponseMessage(
            status=RESPONSE_WARNING,
            message=message,
        )
        if message
        else None
    )


def send_bill_billit(bill_id: str) -> ResponseMessage:
    order_data = BillModel.get_one(bill_id)

    if res := pre_billit_checks(order_data):
        return res

    customer_data = CustomerModel.get_one(order_data.customerId)

    pdf_bytes = pdf.create_bill(order_data, customer_data)
    return send_billit(
        order_data,
        pdf_bytes,
        customer_data,
        callback=lambda response: BillModel.set_external_id(
            bill_id, int(response.json())
        ),
    )
