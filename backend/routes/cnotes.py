from flask import Blueprint, request
from controllers import cnotes as ctrl


cnotes = Blueprint('cnotes', __name__)


@cnotes.route('/api/cnotes', methods=['GET', 'POST'])
def cnotes_route():
    if request.method == 'GET':
        return ctrl.get_cnotes()
    elif request.method == 'POST':
        return ctrl.create_cnote(request.json)
    return None


@cnotes.route('/api/cnotes/<int:cnote_id>', methods=['GET', 'PUT', 'DELETE'])
def cnote_route(cnote_id):
    if request.method == 'GET':
        return ctrl.get_cnote(cnote_id)
    elif request.method == 'PUT':
        return ctrl.update_cnote(cnote_id, request.json)
    elif request.method == 'DELETE':
        return ctrl.delete_cnote(cnote_id)
    return None


@cnotes.route('/api/cnotes/sendPeppol/<int:bill_id>', methods=['POST'])
def cnote_sendPeppol(cnote_id):
    if request.method == 'POST':
        return ctrl.send_cnote_peppol(cnote_id)
    return None