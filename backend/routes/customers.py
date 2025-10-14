from flask import Blueprint, request
from controllers import customers as ctrl


customers = Blueprint('customers', __name__)


@customers.route('/api/customers', methods=['GET', 'POST'])
def customers_all():
    if request.method == 'GET':
        return ctrl.get_customers()
    elif request.method == 'POST':
        return ctrl.create_customer(request.json)
    return None


@customers.route('/api/customers/<int:customer_id>', methods=['GET', 'PUT', 'DELETE'])
def customers_id(customer_id):
    if request.method == 'GET':
        return ctrl.get_customer(customer_id)
    elif request.method == 'PUT':
        return ctrl.update_customer(customer_id, request.json)
    elif request.method == 'DELETE':
        return ctrl.delete_customer(customer_id)
    return None