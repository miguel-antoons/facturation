from flask import jsonify
from models import customers as model
import re


def get_customers():
    customers = model.get_customers(['Numero', 'Nom', 'Prenom', 'Societe', 'Commentaire', 'Codepostal', 'Localite', 'TVA'])
    formatted = []
    for customer in customers:
        formatted.append({
            'id': customer[0],
            'name': customer[1],
            'surname': customer[2],
            'company': customer[3],
            'phones': detect_phones(customer[4]) + detect_mobiles(customer[4]),
            'hasEmail': len(detect_emails(customer[4])) > 0,
            'hasVAT': customer[7] is not None and customer[7] != '',
            'postal_code': customer[5],
            'city': customer[6],
        })
    return jsonify(formatted)


def get_customer(customer_id):
    customer = model.get_customers(
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
    formatted = {
        'id': customer[0][0],
        'name': customer[0][1],
        'surname': customer[0][2],
        'company': customer[0][3],
        'comment': customer[0][4],
        'street': customer[0][5].split(',')[0].strip(),
        'number': ''.join(customer[0][5].split(',')[1:]),
        'postal_code': customer[0][6],
        'city': customer[0][7],
        'vat_number': customer[0][8],
        'language': customer[0][9],
        'architect_name': customer[0][10],
    }
    return jsonify(formatted)


def create_customer(json):
    new_customer = {
        'Numero': model.get_last_customer_id() + 1,
        'Nom': json.get('name'),
        'Prenom': json.get('surname'),
        'Societe': json.get('company'),
        'Commentaire': json.get('comment'),
        'Adresse': f'{json.get('street').strip()} , {json.get('number').strip()}',
        'Codepostal': json.get('postal_code'),
        'Localite': json.get('city'),
        'TVA': json.get('vat_number'),
        'Langue': json.get('language'),
        'Nom Architecte': json.get('architect_name'),
    }
    response = {
        'id': model.create_customer(new_customer),
        'status': 'success',
    }
    return jsonify(response)


def update_customer(customer_id, json):
    updated_customer = {
        'Nom': json.get('name'),
        'Prenom': json.get('surname'),
        'Societe': json.get('company'),
        'Commentaire': json.get('comment'),
        'Adresse': f'{json.get('street').strip()} , {json.get('number').strip()}',
        'Codepostal': json.get('postal_code'),
        'Localite': json.get('city'),
        'TVA': json.get('vat_number'),
        'Langue': json.get('language'),
        'Nom Architecte': json.get('architect_name'),
    }
    model.update_customer(customer_id, updated_customer)
    response = {
        'id': customer_id,
        'status': 'updated',
    }
    return jsonify(response)


def delete_customer(customer_id):
    model.delete_customer(customer_id)
    response = {
        'id': customer_id,
        'status': 'deleted',
    }
    return jsonify(response)


def detect_phones(comment):
    if comment is None:
        return []

    patterns = [
        r'\+\d{10}',
        r'0\d{8}',
        r'0\d{2}/\d{2} \d{2} \d{2}',
        r'0\d{2}/\d{2},\d{2},\d{2}',
        r'0\d{1}/\d{3} \d{2} \d{2}',
        r'0\d{1}/\d{3},\d{2},\d{2}',
    ]
    phone_numbers = []

    for pattern in patterns:
        phone_numbers.extend(re.findall(pattern, comment))

    cleaned_phone_numbers = []
    for number in phone_numbers:
        cleaned_phone_numbers.append(re.sub(r'[^\d+]', '', number))

    return cleaned_phone_numbers


def detect_mobiles(comment):
    if comment is None:
        return []

    patterns = [
        r'\+\d{11}',
        r'0\d{9}',
        r'0\d{3}/\d{2} \d{2} \d{2}',
        r'0\d{3}/\d{2},\d{2},\d{2}',
    ]
    mobile_numbers = []

    for pattern in patterns:
        mobile_numbers.extend(re.findall(pattern, comment))

    cleaned_mobile_numbers = []
    for number in mobile_numbers:
        cleaned_mobile_numbers.append(re.sub(r'[^\d+]', '', number))

    return cleaned_mobile_numbers


def detect_emails(comment):
    if comment is None:
        return []

    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, comment)


def is_old_db_comment(comment):
    if comment is None:
        return True

    return not (comment.startswith('##') and comment.endswith('##'))
