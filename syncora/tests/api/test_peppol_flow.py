"""TC-PEPPOL-1..10 and TC-BILLIT-DEL-4/5 : Peppol send flow.

``POST /api/bills/sendPeppol/{id}`` and ``POST /api/cnotes/sendPeppol/{id}``.
Billit HTTP is mocked; the poller is stubbed via ``poller_spy``.
"""

import json
from typing import TYPE_CHECKING

import pytest
from bson import ObjectId

from tests.api.helpers import insert_bill, insert_cnote
from tests.helpers import make_customer_back

if TYPE_CHECKING:
    import mongomock
    import responses
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore

SEND_URL = "https://billit.test.local/v1/orders/commands/send"


def _register_send_success(
    billit_fake: responses.RequestsMock, status: int = 201
) -> None:
    billit_fake.add(billit_fake.POST, SEND_URL, json={"ok": True}, status=status)


def _send_call_body(billit_fake: responses.RequestsMock) -> dict[str, object]:
    raw = billit_fake.calls[0].request.body
    return json.loads(raw)


# --- Bill Peppol gates (TC-PEPPOL-1..7) ---------------------------------- #
def test_send_peppol_success_sets_unknown_and_polls(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    poller_spy: list[int],
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-1 / TC-BILLIT-DEL-4 / TC-BILLIT-DEL-5
    customer_store.seed(make_customer_back(id=1, vat_number="BE0123456789"))
    bill_id = insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=42, peppol_status=-1
    )
    _register_send_success(billit_fake)

    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    assert resp.get_json()["status"] == "success"
    # local status set to UNKNOWN (0)
    assert (
        mongo["bills"].find_one({"_id": ObjectId(bill_id)})["peppolDeliveryStatus"] == 0
    )
    # poll started
    assert 42 in poller_spy
    # outbound body shape
    body = _send_call_body(billit_fake)
    assert body == {"Transporttype": "Peppol", "OrderIDs": [42]}


def test_send_peppol_not_registered_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-PEPPOL-2
    bill_id = insert_bill(
        mongo, order_number="2026-001", external_id=0, peppol_status=-1
    )
    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.parametrize("status", [1, 2])
def test_send_peppol_already_pending_or_sent_is_warning(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    status: int,
) -> None:
    # TC-PEPPOL-3 / TC-PEPPOL-4
    bill_id = insert_bill(mongo, external_id=42, peppol_status=status)
    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


def test_send_peppol_customer_without_vat_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-5
    customer_store.seed(make_customer_back(id=1, vat_number=""))
    bill_id = insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=42, peppol_status=-1
    )
    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


def test_send_peppol_non_2xx_forwards_error_and_keeps_status(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-6 / TC-NFR-3
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    bill_id = insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=42, peppol_status=-1
    )
    billit_fake.add(billit_fake.POST, SEND_URL, json={"error": "blocked"}, status=400)

    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    body = resp.get_json()
    assert body["status"] == "error"
    assert body["message"] == {"error": "blocked"}
    assert (
        mongo["bills"].find_one({"_id": ObjectId(bill_id)})["peppolDeliveryStatus"]
        == -1
    )


@pytest.mark.gap
def test_send_peppol_non_json_error_body_is_unhandled(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-7 / TC-GAP-5
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    bill_id = insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=42, peppol_status=-1
    )
    billit_fake.add(
        billit_fake.POST, SEND_URL, body="oops", content_type="text/plain", status=500
    )
    with pytest.raises(ValueError):
        client.post(f"/api/bills/sendPeppol/{bill_id}")


# --- Credit-note Peppol gates (TC-PEPPOL-8..10) ------------------------- #
def test_send_cnote_peppol_referenced_invoice_not_sent_is_warning(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-8 : referenced invoice Peppol status != SENT
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=10, peppol_status=0
    )
    cnote_id = insert_cnote(
        mongo,
        order_number="C2026-001",
        customer_id=1,
        external_id=42,
        peppol_status=-1,
        about_invoice_number="2026-001",
    )
    resp = client.post(f"/api/cnotes/sendPeppol/{cnote_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.gap
def test_send_cnote_peppol_missing_referenced_invoice_is_unhandled(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-9 / TC-GAP-3 / TC-NFR-4 : IndexError on missing referenced invoice
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    cnote_id = insert_cnote(
        mongo,
        order_number="C2026-001",
        customer_id=1,
        external_id=42,
        peppol_status=-1,
        about_invoice_number="2026-999",
    )
    with pytest.raises(IndexError):
        client.post(f"/api/cnotes/sendPeppol/{cnote_id}")


def test_send_cnote_peppol_referenced_invoice_sent_succeeds(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    poller_spy: list[int],
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PEPPOL-10
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    insert_bill(
        mongo, order_number="2026-001", customer_id=1, external_id=10, peppol_status=2
    )
    cnote_id = insert_cnote(
        mongo,
        order_number="C2026-001",
        customer_id=1,
        external_id=42,
        peppol_status=-1,
        about_invoice_number="2026-001",
    )
    _register_send_success(billit_fake)

    resp = client.post(f"/api/cnotes/sendPeppol/{cnote_id}")
    assert resp.get_json()["status"] == "success"
    assert (
        mongo["cnotes"].find_one({"_id": ObjectId(cnote_id)})["peppolDeliveryStatus"]
        == 0
    )
    assert 42 in poller_spy
