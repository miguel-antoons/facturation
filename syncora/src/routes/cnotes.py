from flask import Blueprint, Response, abort, jsonify, request

from controllers import cnotes as ctrl

cnotes = Blueprint("cnotes", __name__)


@cnotes.route("/api/cnotes", methods=["GET", "POST"])
def cnotes_route() -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_cnotes()
    elif request.method == "POST":
        res = ctrl.create_cnote(request.json)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@cnotes.route("/api/cnotes/<string:cnote_id>", methods=["GET", "PUT", "DELETE"])
def cnote_route(cnote_id: str) -> Response:
    res = None
    if request.method == "GET":
        res = ctrl.get_cnote(cnote_id)
    elif request.method == "PUT":
        res = ctrl.update_cnote(cnote_id, request.json)
    elif request.method == "DELETE":
        res = ctrl.delete_cnote(cnote_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@cnotes.route("/api/cnotes/sendPeppol/<string:cnote_id>", methods=["POST"])
def cnote_send_peppol(cnote_id: str) -> Response:
    res = None
    if request.method == "POST":
        res = ctrl.send_cnote_peppol(cnote_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)


@cnotes.route("/api/cnotes/sendBillit/<string:cnote_id>", methods=["POST"])
def cnote_send_billit(cnote_id: str) -> Response:
    res = None
    if request.method == "POST":
        res = ctrl.send_cnote_billit(cnote_id)
    else:
        abort(405, description="Method not allowed for this endpoint")
    return jsonify(res)
