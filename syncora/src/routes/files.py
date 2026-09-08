from flask import Blueprint, Response, abort, request

from controllers import files as ctrl
from utils.response_file import make_pdf_response

files = Blueprint("files", __name__)


@files.route("/api/files/customers/<int:customer_id>", methods=["GET"])
def customer_file(customer_id: int) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_customer_file(customer_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return make_pdf_response(res, filename=f"customer_{customer_id}.pdf")


@files.route("/api/files/bills/<string:bill_id>", methods=["GET"])
def bill_file(bill_id: str) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_bill_file(bill_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return make_pdf_response(res, filename=f"bill_{bill_id}.pdf")


@files.route("/api/files/cnotes/<string:cnote_id>", methods=["GET"])
def cnote_file(cnote_id: str) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_cnote_file(cnote_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return make_pdf_response(res, filename=f"cnote_{cnote_id}.pdf")
