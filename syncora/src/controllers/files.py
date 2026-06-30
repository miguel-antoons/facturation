import io

from reportlab.pdfgen.canvas import Canvas

from controllers.bill_gen import create_bill
from controllers.cnote_gen import create_cnote
from models.bills import BillModel
from models.cnotes import CnoteModel
from models.customers import CustomerModel


def get_customer_file(customer_id: int) -> bytes:
    customer_info = CustomerModel.get_one(customer_id)

    pdf_buffer = io.BytesIO()
    canvas = Canvas(pdf_buffer)
    canvas.drawString(100, 800, f"Numéro: {customer_info.id}")
    canvas.drawString(
        100, 780, f"Nom, Prénom: {customer_info.name} {customer_info.surname}"
    )
    canvas.drawString(100, 760, f"Société: {customer_info.company}")
    canvas.drawString(
        100,
        740,
        f"Adresse: {customer_info.street}, {customer_info.number} {customer_info.city}",
    )
    canvas.drawString(100, 720, f"Numéro de TVA: {customer_info.vat_number}")
    canvas.drawString(100, 700, f"Langue: {customer_info.language}")
    canvas.drawString(100, 680, f"Nom d'Architecte: {customer_info.architect_name}")
    canvas.drawString(100, 610, f"Commentaire: {customer_info.comment}")
    canvas.save()

    return pdf_buffer.getvalue()


def get_bill_file(bill_id: str) -> bytes:
    order_data = BillModel.get_one(bill_id)
    customer_data = CustomerModel.get_one(order_data.customerId)
    return create_bill(order_data, customer_data)


def get_cnote_file(cnote_id: str) -> bytes:
    order_data = CnoteModel.get_one(cnote_id)
    customer_data = CustomerModel.get_one(order_data.customerId)
    return create_cnote(order_data, customer_data)
