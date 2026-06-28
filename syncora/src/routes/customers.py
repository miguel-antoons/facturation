from flask import Blueprint, Response, request

from controllers import customers as ctrl

customers = Blueprint("customers", __name__)


@customers.route("/api/customers", methods=["GET", "POST"])
def customers_all() -> Response | None:
    if request.method == "GET":
        return ctrl.get_customers()
    if request.method == "POST":
        return ctrl.create_customer(request.json)
    return None


@customers.route("/api/customers/<int:customer_id>", methods=["GET", "PUT", "DELETE"])
def customers_id(customer_id: int) -> Response | None:
    if request.method == "GET":
        return ctrl.get_customer(customer_id)
    if request.method == "PUT":
        return ctrl.update_customer(customer_id, request.json)
    if request.method == "DELETE":
        return ctrl.delete_customer(customer_id)
    return None
