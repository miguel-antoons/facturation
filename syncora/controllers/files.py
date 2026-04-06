from flask import make_response
from models import customers as model
from reportlab.pdfgen.canvas import Canvas
from controllers.bill_gen import create_bill
from controllers.cnote_gen import create_cnote
from constants.customer_back import *
from models.customers import get_customers_dict
from models.bills import get_bill
from models.cnotes import get_cnote


def get_customer_file(customer_id):
    customer_info = model.get_customers(
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
        ],
        filters={CUSTOMER_DB_ID: customer_id}
    )[0]
    # generate pdf file from customer info
    pdf_file_path = f'/tmp/customer_{customer_id}.pdf'
    canvas = Canvas(pdf_file_path)
    canvas.drawString(100, 800, f"Numéro: {customer_info.id}")
    canvas.drawString(100, 780, f"Nom, Prénom: {customer_info.name} {customer_info.surname}")
    canvas.drawString(100, 760, f"Société: {customer_info.company}")
    canvas.drawString(100, 740, f"Adresse: {customer_info.street}, {customer_info.number} {customer_info.city}")
    canvas.drawString(100, 720, f"Numéro de TVA: {customer_info.vat_number}")
    canvas.drawString(100, 700, f"Langue: {customer_info.language}")
    canvas.drawString(100, 680, f"Nom d'Architecte: {customer_info.architect_name}")
    canvas.drawString(100, 610, f"Commentaire: {customer_info.comment}")
    canvas.save()

    binary_file = open(pdf_file_path, 'rb')
    response = make_response(binary_file)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'inline', filename=f'customer_{customer_id}.pdf')
    return response


def get_bill_file(bill_id: str):
    order_data = get_bill(bill_id)
    customer_data = get_customers_dict(
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
    ).values()
    filename = create_bill(order_data, list(customer_data)[0])
    with open(filename, 'rb') as binary_file:
        resp = make_response(binary_file.read())
    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Content-Disposition', 'inline', filename=filename)
    return resp


def get_cnote_file(cnote_id: str):
    order_data = get_cnote(cnote_id)
    customer_data = get_customers_dict(
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
        filters={CUSTOMER_DB_ID: order_data['Customer']['Numero']}
    ).values()
    filename = create_cnote(order_data, list(customer_data)[0])
    with open(filename, 'rb') as binary_file:
        resp = make_response(binary_file.read())
    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Content-Disposition', 'inline', filename=f'cnote_{cnote_id}.pdf')
    return resp
