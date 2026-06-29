from flask import Blueprint, Response, abort, jsonify, request

from controllers import bills as ctrl

bills = Blueprint("bills", __name__)


@bills.route("/api/bills", methods=["GET", "POST"])
def bills_route() -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_bills()
    elif request.method == "POST":
        res = ctrl.create_bill(request.json)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@bills.route("/api/bills/<string:bill_id>", methods=["GET", "PUT", "DELETE"])
def bill_route(bill_id: str) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_bill(bill_id)
    elif request.method == "PUT":
        res = ctrl.update_bill(bill_id, request.json)
    elif request.method == "DELETE":
        res = ctrl.delete_bill(bill_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@bills.route("/api/bills/sendPeppol/<string:bill_id>", methods=["POST"])
def bill_send_peppol(bill_id: str) -> Response:
    res = None
    if request.method == "POST":
        res = ctrl.send_bill_peppol(bill_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@bills.route("/api/bills/sendBillit/<string:bill_id>", methods=["POST"])
def bill_send_billit(bill_id: str) -> Response:
    res = None
    if request.method == "POST":
        res = ctrl.send_bill_billit(bill_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)
