from flask import Blueprint, Response, abort, jsonify, request

from controllers import customers as ctrl

customers = Blueprint("customers", __name__)


@customers.route("/api/customers", methods=["GET", "POST"])
def customers_all() -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_customers()
    elif request.method == "POST":
        res = ctrl.create_customer(request.json)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@customers.route("/api/customers/<int:customer_id>", methods=["GET", "PUT", "DELETE"])
def customers_id(customer_id: int) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_customer(customer_id)
    elif request.method == "PUT":
        res = ctrl.update_customer(customer_id, request.json)
    elif request.method == "DELETE":
        res = ctrl.delete_customer(customer_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)
