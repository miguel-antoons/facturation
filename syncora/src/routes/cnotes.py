from flask import Blueprint, Response, request

from controllers import cnotes as ctrl

cnotes = Blueprint("cnotes", __name__)


@cnotes.route("/api/cnotes", methods=["GET", "POST"])
def cnotes_route() -> Response | None:
    if request.method == "GET":
        return ctrl.get_cnotes()
    if request.method == "POST":
        return ctrl.create_cnote(request.json)
    return None


@cnotes.route("/api/cnotes/<string:cnote_id>", methods=["GET", "PUT", "DELETE"])
def cnote_route(cnote_id: str) -> Response | None:
    if request.method == "GET":
        return ctrl.get_cnote(cnote_id)
    if request.method == "PUT":
        return ctrl.update_cnote(cnote_id, request.json)
    if request.method == "DELETE":
        return ctrl.delete_cnote(cnote_id)
    return None


@cnotes.route("/api/cnotes/sendPeppol/<string:cnote_id>", methods=["POST"])
def cnote_send_peppol(cnote_id: str) -> Response | None:
    if request.method == "POST":
        return ctrl.send_cnote_peppol(cnote_id)
    return None


@cnotes.route("/api/cnotes/sendBillit/<string:cnote_id>", methods=["POST"])
def cnote_send_billit(cnote_id: str) -> Response | None:
    if request.method == "POST":
        return ctrl.send_cnote_billit(cnote_id)
    return None
