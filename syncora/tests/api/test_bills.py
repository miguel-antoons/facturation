"""TC-BILL-1..27 : bill REST contract (FR-BILL-1..8, API-BILL-1..5)."""

from typing import TYPE_CHECKING

import pytest
from bson import ObjectId

from tests.api.helpers import insert_bill
from tests.helpers import make_bill_payload, make_customer_back, valid_object_id_str
from utils.generic_error import SyncoraError

if TYPE_CHECKING:
    import mongomock
    import responses
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore

SHORT_KEYS = {"orderId", "customerName", "orderNumber", "orderDate", "orderTitle"}
# Keys actually present in OrderBack.to_front() for a bill. NOTE: the spec
# (§3.5 / TC-BILL-15) lists totalExcl/totalVAT/totalIncl here, but the
# implementation excludes them -- see tests/findings.md.
BILL_FRONT_KEYS = {
    "billitSent",
    "customerId",
    "deliveryDate",
    "expiryDate",
    "orderDate",
    "orderLines",
    "orderNumber",
    "orderTitle",
    "peppolDeliveryStatus",
    "ventilationCode",
}
LINE_FRONT_KEYS = {"VATPercentage", "description", "quantity", "unit", "unitPriceExcl"}


# --- List bills (TC-BILL-1..4) ------------------------------------------- #
def test_list_bills_short_rows(
    client: FlaskClient, customer_store: FakeCustomerStore, mongo: mongomock.Database
) -> None:
    # TC-BILL-1
    customer_store.seed(make_customer_back(id=1, name="Dupont", surname="Luc"))
    insert_bill(mongo, order_number="2026-001", customer_id=1)
    insert_bill(mongo, order_number="2026-002", customer_id=1)

    items = client.get("/api/bills").get_json()
    assert len(items) == 2
    for item in items:
        assert set(item.keys()) == SHORT_KEYS


def test_list_bills_customer_name_formatting(
    client: FlaskClient, customer_store: FakeCustomerStore, mongo: mongomock.Database
) -> None:
    # TC-BILL-2 : "name surname, company" / "name surname"
    customer_store.seed(
        make_customer_back(id=1, name="Luc", surname="Dupont", company="Acme")
    )
    customer_store.seed(
        make_customer_back(id=2, name="Jane", surname="Doe", company="")
    )
    insert_bill(mongo, order_number="2026-001", customer_id=1)
    insert_bill(mongo, order_number="2026-002", customer_id=2)

    items = {b["orderNumber"]: b for b in client.get("/api/bills").get_json()}
    assert items["2026-001"]["customerName"] == "Luc Dupont, Acme"
    assert items["2026-002"]["customerName"] == "Jane Doe"


def test_list_bills_empty(client: FlaskClient) -> None:
    # TC-BILL-3
    assert client.get("/api/bills").get_json() == []


@pytest.mark.gap
def test_list_bills_unknown_customer_is_unhandled(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-4 : bill references a customer not in the store -> KeyError
    insert_bill(mongo, order_number="2026-001", customer_id=999)
    with pytest.raises(KeyError):
        client.get("/api/bills")


# --- Create / update (TC-BILL-5..14) ------------------------------------ #
def test_create_bill_sets_defaults(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-5 / TC-NFR-9
    resp = client.post("/api/bills", json=make_bill_payload())
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    bill_id = body["id"]
    doc = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
    assert doc["externalId"] == 0
    assert doc["peppolDeliveryStatus"] == -1


def test_create_bill_empty_order_number(client: FlaskClient) -> None:
    # TC-BILL-6
    resp = client.post("/api/bills", json=make_bill_payload(order_number=""))
    assert resp.get_json()["status"] == "success"


def test_update_bill_same_order_number(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-7
    bill_id = insert_bill(mongo, order_number="2026-001")
    resp = client.put(
        f"/api/bills/{bill_id}", json=make_bill_payload(order_number="2026-001")
    )
    assert resp.get_json()["status"] == "success"


def test_update_bill_to_free_order_number(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-8
    bill_id = insert_bill(mongo, order_number="2026-001")
    resp = client.put(
        f"/api/bills/{bill_id}", json=make_bill_payload(order_number="2026-999")
    )
    assert resp.get_json()["status"] == "success"


def test_create_bill_duplicate_order_number_rejected(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-9
    insert_bill(mongo, order_number="2026-001")
    resp = client.post("/api/bills", json=make_bill_payload(order_number="2026-001"))
    body = resp.get_json()
    assert body["status"] == "error"
    assert "message" in body


def test_update_bill_to_used_order_number_rejected(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-10
    insert_bill(mongo, order_number="2026-002")
    bill_id = insert_bill(mongo, order_number="2026-001")
    resp = client.put(
        f"/api/bills/{bill_id}", json=make_bill_payload(order_number="2026-002")
    )
    assert resp.get_json()["status"] == "error"


def test_update_locked_bill_is_warning_and_unchanged(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-11
    bill_id = insert_bill(
        mongo, order_number="2026-001", external_id=5, order_title="Original"
    )
    resp = client.put(
        f"/api/bills/{bill_id}",
        json=make_bill_payload(order_number="2026-001", order_title="Changed"),
    )
    assert resp.get_json()["status"] == "warning"
    doc = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
    assert doc["orderTitle"] == "Original"


@pytest.mark.gap
def test_update_nonexistent_bill_is_unhandled(client: FlaskClient) -> None:
    # TC-BILL-12 / TC-GAP-1 : get_one raises before .locked is reached
    with pytest.raises(SyncoraError):
        client.put(f"/api/bills/{valid_object_id_str()}", json=make_bill_payload())


def test_create_bill_empty_order_lines(client: FlaskClient) -> None:
    # TC-BILL-13 : create does not gate on orderLines
    resp = client.post("/api/bills", json=make_bill_payload(lines=[]))
    assert resp.get_json()["status"] == "success"


def test_create_bill_returns_string_id(client: FlaskClient) -> None:
    # TC-BILL-14
    body = client.post("/api/bills", json=make_bill_payload()).get_json()
    assert isinstance(body["id"], str)


# --- Get one bill (TC-BILL-15..21) --------------------------------------- #
def test_get_bill_front_shape(client: FlaskClient, mongo: mongomock.Database) -> None:
    # TC-BILL-15
    bill_id = insert_bill(mongo, order_number="2026-001")
    body = client.get(f"/api/bills/{bill_id}").get_json()
    assert set(body.keys()) == BILL_FRONT_KEYS
    assert "orderId" not in body
    assert "externalId" not in body
    assert set(body["orderLines"][0].keys()) == LINE_FRONT_KEYS


def test_get_bill_triggers_poll_when_pending(
    client: FlaskClient,
    mongo: mongomock.Database,
    poller_spy: list[int],
) -> None:
    # TC-BILL-16 / TC-POLL-8
    bill_id = insert_bill(mongo, external_id=42, peppol_status=1)
    client.get(f"/api/bills/{bill_id}")
    assert 42 in poller_spy


def test_get_bill_triggers_poll_when_unknown(
    client: FlaskClient,
    mongo: mongomock.Database,
    poller_spy: list[int],
) -> None:
    # TC-BILL-17
    bill_id = insert_bill(mongo, external_id=42, peppol_status=0)
    client.get(f"/api/bills/{bill_id}")
    assert 42 in poller_spy


@pytest.mark.parametrize("status", [-1, 2])
def test_get_bill_does_not_poll_when_not_sent_or_sent(
    client: FlaskClient,
    mongo: mongomock.Database,
    poller_spy: list[int],
    status: int,
) -> None:
    # TC-BILL-18 / TC-BILL-19 / TC-POLL-9
    bill_id = insert_bill(mongo, external_id=42, peppol_status=status)
    client.get(f"/api/bills/{bill_id}")
    assert poller_spy == []


@pytest.mark.gap
def test_get_bill_nonexistent_is_unhandled(client: FlaskClient) -> None:
    # TC-BILL-20 / TC-GAP-2
    with pytest.raises(SyncoraError):
        client.get(f"/api/bills/{valid_object_id_str()}")


@pytest.mark.gap
def test_get_bill_response_omits_totals(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    # TC-BILL-21 : the spec expects totalExcl/totalVAT/totalIncl in the
    # response, but to_front() excludes them. Pinned here; see findings.md.
    bill_id = insert_bill(mongo, order_number="2026-001")
    body = client.get(f"/api/bills/{bill_id}").get_json()
    for total in ("totalExcl", "totalVAT", "totalIncl"):
        assert total not in body


def test_get_bill_totals_are_non_negative_via_model(mongo: mongomock.Database) -> None:
    # TC-BILL-21 (model-level): totals are non-negative and the VAT identity
    # holds. The HTTP response omits totals (see test above), so verify on the
    # model that backs the response.
    from models.bills import BillModel

    insert_bill(
        mongo,
        order_lines=[
            {
                "description": "a",
                "quantity": 1,
                "unitPriceExcl": 100.0,
                "unit": "h",
                "VATPercentage": 6.0,
            }
        ],
    )
    order = BillModel.get_one(BillModel.get()[0].orderId)
    assert order.total_excl >= 0
    assert order.total_incl >= 0
    assert order.total_vat == order.total_incl - order.total_excl


# --- Delete bill (TC-BILL-22..27) ---------------------------------------- #
def test_delete_unregistered_bill_no_billit_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILL-22
    bill_id = insert_bill(mongo, external_id=0, peppol_status=-1)
    resp = client.delete(f"/api/bills/{bill_id}")
    assert resp.get_json()["status"] == "success"
    assert mongo["bills"].find_one({"_id": ObjectId(bill_id)}) is None
    assert len(billit_fake.calls) == 0


def test_delete_registered_bill_calls_billit_and_removes_locally(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    fake_env: dict[str, str],
) -> None:
    # TC-BILL-23 / TC-BILLIT-DEL-1
    bill_id = insert_bill(mongo, external_id=42, peppol_status=-1)
    billit_fake.add(
        billit_fake.DELETE,
        f"{fake_env['URL']}/orders/42",
        body="true",
        status=200,
    )
    resp = client.delete(f"/api/bills/{bill_id}")
    assert resp.get_json()["status"] == "success"
    assert mongo["bills"].find_one({"_id": ObjectId(bill_id)}) is None
    assert len(billit_fake.calls) == 1
    assert billit_fake.calls[0].request.method == "DELETE"


@pytest.mark.parametrize("status", [0, 1, 2])
def test_delete_undeletable_bill_is_warning_and_kept(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    status: int,
) -> None:
    # TC-BILL-24
    bill_id = insert_bill(mongo, external_id=42, peppol_status=status)
    resp = client.delete(f"/api/bills/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert mongo["bills"].find_one({"_id": ObjectId(bill_id)}) is not None
    assert len(billit_fake.calls) == 0


def test_delete_bill_billit_failure_aborts_local_delete(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    fake_env: dict[str, str],
) -> None:
    # TC-BILL-25 / TC-BILLIT-DEL-2
    bill_id = insert_bill(mongo, external_id=42, peppol_status=-1)
    billit_fake.add(
        billit_fake.DELETE,
        f"{fake_env['URL']}/orders/42",
        body="false",
        status=200,
    )
    resp = client.delete(f"/api/bills/{bill_id}")
    assert resp.get_json()["status"] == "error"
    assert mongo["bills"].find_one({"_id": ObjectId(bill_id)}) is not None


@pytest.mark.gap
def test_delete_nonexistent_bill_is_unhandled(client: FlaskClient) -> None:
    # TC-BILL-26
    with pytest.raises(SyncoraError):
        client.delete(f"/api/bills/{valid_object_id_str()}")


def test_delete_bill_local_zero_rows_is_error(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    fake_env: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # TC-BILL-27 : Billit returns true but the local delete touches 0 rows
    from models.bills import BillModel

    bill_id = insert_bill(mongo, external_id=42, peppol_status=-1)
    billit_fake.add(
        billit_fake.DELETE,
        f"{fake_env['URL']}/orders/42",
        body="true",
        status=200,
    )
    monkeypatch.setattr(BillModel, "delete", staticmethod(lambda _order_id: False))
    resp = client.delete(f"/api/bills/{bill_id}")
    assert resp.get_json()["status"] == "error"
