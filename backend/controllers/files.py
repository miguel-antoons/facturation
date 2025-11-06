from flask import make_response, json
from models import customers as model
from reportlab.pdfgen.canvas import Canvas
from controllers.bills import get_bill
from controllers.bill_gen import create_bill
from controllers.cnotes import get_cnote
from controllers.cnote_gen import create_cnote


def get_customer_file(customer_id):
    # get customer info
    customer_info = model.get_customers(
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
            'Nom Architecte',
        ],
        filters={'Numero': customer_id}
    )
    # generate pdf file from customer info
    pdf_file_path = f'/tmp/customer_{customer_id}.pdf'
    canvas = Canvas(pdf_file_path)
    canvas.drawString(100, 800, f"Numéro: {customer_info[0][0]}")
    canvas.drawString(100, 780, f"Nom, Prénom: {customer_info[0][1]} {customer_info[0][2]}")
    canvas.drawString(100, 760, f"Société: {customer_info[0][3]}")
    canvas.drawString(100, 740, f"Adresse: {customer_info[0][5]}, {customer_info[0][6]} {customer_info[0][7]}")
    canvas.drawString(100, 720, f"Numéro de TVA: {customer_info[0][8]}")
    canvas.drawString(100, 700, f"Langue: {customer_info[0][9]}")
    canvas.drawString(100, 680, f"Nom d'Architecte: {customer_info[0][10]}")
    canvas.drawString(100, 610, f"Commentaire: {customer_info[0][4]}")
    canvas.save()

    binary_file = open(pdf_file_path, 'rb')
    response = make_response(binary_file)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'inline', filename=f'customer_{customer_id}.pdf')
    return response


def get_bill_file(bill_id):
    req_data = get_bill(bill_id)
    filename = create_bill(req_data)
    binary_file = open(filename, 'rb')
    resp = make_response(binary_file)
    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Content-Disposition', 'inline', filename=f'bill_{bill_id}.pdf')
    return resp


def get_cnote_file(cnote_id):
    req_data = get_cnote(cnote_id)
    filename = create_cnote(req_data)
    binary_file = open(filename, 'rb')
    resp = make_response(binary_file)
    resp.headers.set('Content-Type', 'application/pdf')
    resp.headers.set('Content-Disposition', 'inline', filename=f'cnote_{cnote_id}.pdf')
    return resp