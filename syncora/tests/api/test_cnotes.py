"""TC-CN-1..9 : credit-note REST contract (FR-CN-1..6, API-CN-1..5).

Credit notes mirror bills; only the deltas are tested here. Uniqueness is
per-collection (bills and cnotes are independent).
"""

from typing import TYPE_CHECKING

import pytest
from bson import ObjectId

from tests.api.helpers import insert_bill, insert_cnote
from tests.helpers import make_cnote_payload

if TYPE_CHECKING:
    import mongomock
    import responses
    from flask.testing import FlaskClient

CNOTE_FRONT_KEYS = {
    "billitSent",
    "customerId",
    "expiryDate",
    "orderDate",
    "orderLines",
    "orderNumber",
    "orderTitle",
    "peppolDeliveryStatus",
    "ventilationCode",
    "aboutInvoiceNumber",
}


def test_create_cnote_persists_about_invoice_number(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-CN-1
    resp = client.post("/api/cnotes", json=make_cnote_payload())
    assert resp.get_json()["status"] == "success"
    doc = mongo["cnotes"].find_one({"_id": ObjectId(resp.get_json()["id"])})
    assert doc["aboutInvoiceNumber"] == "2026-001"


def test_bill_without_about_invoice_number_is_not_a_cnote(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-CN-2 : a bill's to_front omits aboutInvoiceNumber
    bill_id = insert_bill(mongo, order_number="2026-001")
    body = client.get(f"/api/bills/{bill_id}").get_json()
    assert "aboutInvoiceNumber" not in body


def test_get_cnote_includes_about_invoice_number(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-CN-3
    cnote_id = insert_cnote(mongo, order_number="C2026-001")
    body = client.get(f"/api/cnotes/{cnote_id}").get_json()
    assert set(body.keys()) == CNOTE_FRONT_KEYS
    assert body["aboutInvoiceNumber"] == "2026-001"
    # formatted_delivery_date is a model property (not serialized); see
    # test_cnote_ogm_and_delivery_date_empty for the model-level assertion.


def test_cnote_ogm_and_delivery_date_empty(mongo: mongomock.Database) -> None:
    # TC-CN-4 / TC-CN-5 : credit notes have no OGM and no delivery date
    from models.cnotes import CnoteModel

    cnote_id = insert_cnote(mongo, order_number="C2026-001")
    order = CnoteModel.get_one(cnote_id)
    assert order.ogm == ""
    assert order.formatted_delivery_date == ""
    assert order.is_cnote is True


@pytest.mark.parametrize("status", [0, 1, 2])
def test_delete_undeletable_cnote_is_warning_and_kept(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    status: int,
) -> None:
    # TC-CN-6
    cnote_id = insert_cnote(mongo, external_id=42, peppol_status=status)
    resp = client.delete(f"/api/cnotes/{cnote_id}")
    assert resp.get_json()["status"] == "warning"
    assert mongo["cnotes"].find_one({"_id": ObjectId(cnote_id)}) is not None
    assert len(billit_fake.calls) == 0


def test_update_locked_cnote_is_warning_and_unchanged(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-CN-7
    cnote_id = insert_cnote(
        mongo, order_number="C2026-001", external_id=5, order_title="Original"
    )
    resp = client.put(
        f"/api/cnotes/{cnote_id}",
        json=make_cnote_payload(order_number="C2026-001", order_title="Changed"),
    )
    assert resp.get_json()["status"] == "warning"
    doc = mongo["cnotes"].find_one({"_id": ObjectId(cnote_id)})
    assert doc["orderTitle"] == "Original"


def test_create_cnote_duplicate_order_number_rejected(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-CN-8
    insert_cnote(mongo, order_number="C2026-001")
    resp = client.post("/api/cnotes", json=make_cnote_payload(order_number="C2026-001"))
    assert resp.get_json()["status"] == "error"


def test_same_order_number_in_bills_and_cnotes_both_succeed(
    client: FlaskClient,
    mongo: mongomock.Database,
) -> None:
    # TC-CN-9 : uniqueness is per-collection, not cross-collection
    insert_bill(mongo, order_number="2026-001")
    resp = client.post("/api/cnotes", json=make_cnote_payload(order_number="2026-001"))
    assert resp.get_json()["status"] == "success"
