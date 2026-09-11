import controllers.cnote_gen as pdf
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
    ORDER_BACK_ORDER_NUMBER,
    PEPPOL_DELIVERY_STATUS_PENDING,
    PEPPOL_DELIVERY_STATUS_SENT,
    PEPPOL_DELIVERY_STATUS_UNKNOWN,
)
from constants.order_front import OrderFront, OrderFrontShort
from controllers import billit
from controllers.billit import send_peppol
from models.bills import BillModel
from models.cnotes import CnoteModel
from models.customers import CustomerModel
from src.constants.cnote_back import CnoteBack
from utils.peppol_poller import PeppolStatusPoller


def create_cnote(json: OrderFront, db_id: str = "") -> ResponseMessage:
    cnote = CnoteBack.model_validate(json)
    existing = CnoteModel.get_one(db_id) if db_id else None

    # Reject a duplicate order number, unless it belongs to the credit note
    # being edited.
    if CnoteModel.contains(cnote.orderNumber) and (
        existing is None or existing.orderNumber != cnote.orderNumber
    ):
        return ResponseMessage(
            status=RESPONSE_ERROR,
            message=(
                f"Une note de crédit avec le numéro {json.get('orderNumber')} "
                "existe déjà. Veuillez choisir un numéro de facture unique."
            ),
        )

    if not db_id:
        db_id = CnoteModel.create(cnote)
    else:
        if existing.locked:
            return ResponseMessage(
                status=RESPONSE_WARNING,
                message=(
                    f"Note de crédit avec l'ID {existing.orderNumber} a déjà été "
                    "envoyée à Billit et est verrouillée."
                ),
            )
        _ = CnoteModel.update(db_id, cnote)

    return ResponseMessage(
        status=RESPONSE_SUCCESS,
        id=db_id,
    )


def get_cnote(cnote_id: str) -> dict:
    order_back = CnoteModel.get_one(cnote_id)
    if (
        order_back.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_PENDING
        or order_back.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_UNKNOWN
    ):
        PeppolStatusPoller(CnoteModel.set_peppol_status)(order_back.externalId)

    return order_back.to_front()


def get_cnotes() -> list[OrderFrontShort]:
    cnotes = CnoteModel.get()
    customers = CustomerModel.get(
        [
            CUSTOMER_DB_NAME,
            CUSTOMER_DB_FIRSTNAME,
            CUSTOMER_DB_COMPANY,
        ],
        by_id=True,
    )
    cnotes_front = []
    for cnote in cnotes:
        cust_id = cnote.customerId
        name = customers[cust_id].name or ""
        surname = customers[cust_id].surname or ""
        customer_name = f"{name} {surname}".strip()
        customer_name += ", " if customer_name and customers[cust_id].company else ""
        customer_name += (
            f"{customers[cust_id].company}" if customers[cust_id].company else ""
        )
        cnotes_front.append(
            OrderFrontShort(
                orderId=str(cnote.orderId),
                customerName=customer_name,
                orderNumber=cnote.orderNumber,
                orderDate=cnote.orderDate,
                orderTitle=cnote.orderTitle,
            )
        )
    return cnotes_front


def update_cnote(cnote_id: str, json: OrderFront) -> ResponseMessage:
    return create_cnote(json, db_id=cnote_id)


def delete_cnote(cnote_id: str) -> ResponseMessage:
    order_data = CnoteModel.get_one(cnote_id)
    if order_data.undeletable:
        return ResponseMessage(
            status=RESPONSE_WARNING,
            message=(
                f"Note de crédit avec l'ID {order_data.orderNumber} a déjà été "
                "envoyée à Billit et est verrouillée."
            ),
        )
    if order_data.externalId and (res := billit.delete_order(order_data.externalId)):
        return res
    cnote_deleted = CnoteModel.delete(cnote_id)
    if not cnote_deleted:
        print("ERROR: Credit note not deleted from local DB")
    return ResponseMessage(status=RESPONSE_SUCCESS if cnote_deleted else RESPONSE_ERROR)


def pre_peppol_checks(order_data: CnoteBack) -> ResponseMessage | None:
    message = None
    if not order_data.externalId:
        message = (
            f"Note de crédit avec l'ID {order_data.orderNumber} n'est pas encore "
            "enregistré sur Billit. Veuillez d'abord enregistrer la note "
            "de crédit avant de l'envoyer via Peppol."
        )
    elif (
        order_data.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_PENDING
        or order_data.peppolDeliveryStatus == PEPPOL_DELIVERY_STATUS_SENT
    ):
        message = (
            f"Note de crédit avec l'ID {order_data.orderNumber} a déjà été "
            "envoyée à Peppol. Impossible de la ré-envoyer."
        )
    elif not CustomerModel.get_one(order_data.customerId).vat_number:
        message = (
            f"Le client associé à la note de crédit avec l'ID "
            f"{order_data.orderNumber} n'a pas de numéro de TVA. Veuillez ajouter "
            "un numéro de TVA au client avant d'envoyer la facture à Peppol."
        )
    elif (
        BillModel.get({ORDER_BACK_ORDER_NUMBER: order_data.aboutInvoiceNumber})[
            0
        ].peppolDeliveryStatus
        != PEPPOL_DELIVERY_STATUS_SENT
    ):
        message = (
            f"La facture associé à la note de crédit avec l'ID "
            f"{order_data.orderNumber} n'a pas encore été envoyée à Peppol. "
            "Veuillez d'abord l'envoyer à Peppol avant d'envoyer la note de crédit."
        )

    return (
        ResponseMessage(
            status=RESPONSE_WARNING,
            message=message,
        )
        if message
        else None
    )


def send_cnote_peppol(cnote_id: str) -> ResponseMessage:
    order_data: CnoteBack = CnoteModel.get_one(cnote_id)
    if res := pre_peppol_checks(order_data):
        return res
    response = send_peppol(order_data.externalId)
    if response.status_code in [200, 201]:
        CnoteModel.set_peppol_status(
            order_data.externalId, PEPPOL_DELIVERY_STATUS_UNKNOWN
        )
        PeppolStatusPoller(CnoteModel.set_peppol_status)(order_data.externalId)
        return ResponseMessage(status=RESPONSE_SUCCESS)
    print(response.text)
    return ResponseMessage(status=RESPONSE_ERROR, message=response.json())


def pre_billit_checks(order_data: CnoteBack) -> ResponseMessage | None:  # noqa: C901
    message = None
    if order_data.locked:
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} a déjà été "
            "envoyée à Billit et est verrouillée."
        )
    elif not order_data.orderNumber:
        message = (
            f"La note de crédit avec l'ID {order_data.orderId} n'a pas de "
            "numéro de note de crédit. Veuillez ajouter un numéro de note "
            "de crédit avant de l'envoyer à Billit."
        )
    elif not order_data.customerId:
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} n'a pas "
            "de client associé. Veuillez associer un client avant de "
            "l'envoyer à Billit."
        )
    elif not order_data.orderTitle:
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} n'a pas de "
            "titre. Veuillez ajouter un titre avant de l'envoyer à Billit."
        )
    elif not order_data.ventilationCode:
        message = (
            f"Facture avec l'ID {order_data.orderNumber} n'a pas de code de "
            "taux de TVA valide. Veuillez ajouter un taux de TVA valide avant "
            "de l'envoyer à Billit."
        )
    elif not order_data.aboutInvoiceNumber:
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} n'a pas "
            "de numéro de facture associé. Veuillez ajouter un numéro de "
            "facture associé avant de l'envoyer à Billit."
        )
    elif not len(order_data.orderLines):
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} n'a pas "
            "de lignes de note de crédit. Veuillez ajouter au moins une ligne "
            "de commande avant de l'envoyer à Billit."
        )
    elif not BillModel.contains(order_data.aboutInvoiceNumber):
        message = (
            f"La note de crédit avec l'ID {order_data.orderNumber} fait "
            "référence à une facture qui n'a pas encore été envoyée à Billit. "
            "Veuillez d'abord envoyer la facture associée à Billit avant "
            "d'envoyer la note de crédit."
        )
    elif len(order_data.orderLines):
        for line in order_data.orderLines:
            if not line.description:
                message = (
                    f"La note de crédit avec l'ID {order_data.orderNumber} a une "
                    "ligne de commande sans description. Veuillez ajouter une "
                    "description à toutes les lignes de commande avant de l'envoyer "
                    "à Billit."
                )
                break
            if not line.quantity or line.quantity <= 0:
                message = (
                    f"La note de crédit avec l'ID {order_data.orderNumber} a une "
                    "ligne de commande avec une quantité invalide. Veuillez ajouter "
                    "une quantité valide à toutes les lignes de commande avant de "
                    "l'envoyer à Billit."
                )
                break
            if not line.unitPriceExcl or line.unitPriceExcl < 0:
                message = (
                    f"La note de crédit avec l'ID {order_data.orderNumber} a une "
                    "ligne de commande avec un prix unitaire hors taxe invalide. "
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


def send_cnote_billit(bill_id: str) -> ResponseMessage:
    order_data = CnoteModel.get_one(bill_id)

    if res := pre_billit_checks(order_data):
        return res

    customer_data = CustomerModel.get_one(order_data.customerId)

    pdf_bytes = pdf.create_cnote(order_data, customer_data)
    return billit.send_billit(
        order_data,
        pdf_bytes,
        customer_data=customer_data,
        callback=lambda response: CnoteModel.set_external_id(
            bill_id, int(response.json())
        ),
    )
