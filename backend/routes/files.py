from flask import Blueprint, request
from controllers import files as ctrl

files = Blueprint('files', __name__)


@files.route('/api/files/customers/<int:customer_id>', methods=['GET'])
def customer_file(customer_id):
    if request.method == 'GET':
        return ctrl.get_customer_file(customer_id)
    return None


@files.route('/api/files/bills/<int:bill_id>', methods=['GET'])
def bill_file(bill_id):
    if request.method == 'GET':
        return ctrl.get_bill_file(bill_id)
    return None
