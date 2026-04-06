from flask import Blueprint, request, Response
from controllers import bills as ctrl


bills = Blueprint('bills', __name__)


@bills.route('/api/bills', methods=['GET', 'POST'])
def bills_route() -> Response | None:
    if request.method == 'GET':
        return ctrl.get_bills()
    elif request.method == 'POST':
        return ctrl.create_bill(request.json)
    return None


@bills.route('/api/bills/<string:bill_id>', methods=['GET', 'PUT', 'DELETE'])
def bill_route(bill_id: str) -> Response | None:
    if request.method == 'GET':
        return ctrl.get_bill(bill_id)
    elif request.method == 'PUT':
        return ctrl.update_bill(bill_id, request.json)
    elif request.method == 'DELETE':
        return ctrl.delete_bill(bill_id)
    return None


@bills.route('/api/bills/sendPeppol/<string:bill_id>', methods=['POST'])
def bill_send_peppol(bill_id: str) -> Response | None:
    if request.method == 'POST':
        return ctrl.send_bill_peppol(bill_id)
    return None


@bills.route('/api/bills/sendBillit/<string:bill_id>', methods=['POST'])
def bill_send_billit(bill_id: str) -> Response | None:
    if request.method == 'POST':
        return ctrl.send_bill_billit(bill_id)
    return None
