"""TC-BILLIT-1..27 and TC-BILLIT-DEL-* : Billit registration flow.

``POST /api/bills/sendBillit/{id}`` and ``POST /api/cnotes/sendBillit/{id}``.
PDF generation is stubbed (``fake_pdf``); Billit HTTP is mocked
(``billit_fake``). Tests assert on the outbound request and persisted state.
"""

import base64
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

BILLIT_ORDERS_URL = "https://billit.test.local/v1/orders"


@pytest.fixture
def seeded_customer(customer_store: FakeCustomerStore) -> None:
    """A customer with all address fields (required by CustomerBillit)."""
    customer_store.seed(make_customer_back(id=1))


def _register_orders_success(
    billit_fake: responses.RequestsMock, *, body: int = 12345
) -> None:
    billit_fake.add(billit_fake.POST, BILLIT_ORDERS_URL, json=body, status=201)


def _orders_call_body(billit_fake: responses.RequestsMock) -> dict[str, object]:
    assert billit_fake.calls, "expected an outbound POST /orders"
    raw = billit_fake.calls[0].request.body
    return json.loads(raw)


# --- Sunny bill registration (TC-BILLIT-1, 16, 17-bill, 18, NFR-12) ------- #
@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_billit_success_persists_external_id_and_locks(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-1
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=1)
    _register_orders_success(billit_fake, body=12345)

    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "success"
    doc = mongo["bills"].find_one({"_id": ObjectId(bill_id)})
    assert doc["externalId"] == 12345
    # now locked
    from models.bills import BillModel

    assert BillModel.get_one(bill_id).locked is True


@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_billit_attaches_pdf_and_headers(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    fake_env: dict[str, str],
) -> None:
    # TC-BILLIT-16 / TC-NFR-12
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=1)
    _register_orders_success(billit_fake)

    client.post(f"/api/bills/sendBillit/{bill_id}")
    body = _orders_call_body(billit_fake)

    # PDF attached as base64 OrderPDF (TC-BILLIT-16)
    assert "OrderPDF" in body
    pdf = body["OrderPDF"]
    assert pdf["FileName"]
    assert base64.b64decode(pdf["FileContent"]) == b"%PDF-1.4 fake"

    # OrderType / OrderDirection (TC-BILLIT-17 bill / TC-BILLIT-18)
    assert body["OrderType"] == "Invoice"
    assert body["OrderDirection"] == "Income"

    # Auth headers on every Billit call (TC-NFR-12)
    headers = billit_fake.calls[0].request.headers
    assert headers["apiKey"] == fake_env["API_SECRET"]
    assert headers["partyID"] == fake_env["PARTY_ID"]


# --- pre_billit_checks gates (TC-BILLIT-2..12) --------------------------- #
@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_locked_bill_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-2
    bill_id = insert_bill(mongo, order_number="2026-001", external_id=5)
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_missing_order_number_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-3
    bill_id = insert_bill(mongo, order_number="")
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_missing_customer_id_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-4
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=0)
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_missing_title_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-5
    bill_id = insert_bill(mongo, order_number="2026-001", order_title="")
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_missing_ventilation_code_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-6
    bill_id = insert_bill(mongo, order_number="2026-001", ventilation_code="")
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_empty_order_lines_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-7
    bill_id = insert_bill(mongo, order_number="2026-001", order_lines=[])
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.parametrize(
    "bad_line",
    [
        {
            "description": "",
            "quantity": 1,
            "unitPriceExcl": 100.0,
            "unit": "h",
            "VATPercentage": 6.0,
        },  # TC-BILLIT-8
        {
            "description": "d",
            "quantity": 0,
            "unitPriceExcl": 100.0,
            "unit": "h",
            "VATPercentage": 6.0,
        },  # TC-BILLIT-9
        {
            "description": "d",
            "quantity": 1,
            "unitPriceExcl": -1.0,
            "unit": "h",
            "VATPercentage": 6.0,
        },  # TC-BILLIT-10
        {
            "description": "d",
            "quantity": 1,
            "unitPriceExcl": 0.0,
            "unit": "h",
            "VATPercentage": 6.0,
        },  # TC-BILLIT-11
    ],
    ids=["empty-description", "zero-quantity", "negative-price", "zero-price"],
)
@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_invalid_line_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    bad_line: dict[str, object],
) -> None:
    bill_id = insert_bill(mongo, order_number="2026-001", order_lines=[bad_line])
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_billit_second_line_invalid_is_warning_no_call(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-12 : first line valid, second invalid
    good = {
        "description": "d",
        "quantity": 1,
        "unitPriceExcl": 100.0,
        "unit": "h",
        "VATPercentage": 6.0,
    }
    bad = {
        "description": "",
        "quantity": 1,
        "unitPriceExcl": 100.0,
        "unit": "h",
        "VATPercentage": 6.0,
    }
    bill_id = insert_bill(mongo, order_number="2026-001", order_lines=[good, bad])
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


# --- Billit error responses (TC-BILLIT-13..15) -------------------------- #
@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_billit_non_2xx_forwards_error_and_keeps_external_id(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-13 / TC-NFR-3
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=1)
    billit_fake.add(
        billit_fake.POST, BILLIT_ORDERS_URL, json={"error": "nope"}, status=400
    )
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    body = resp.get_json()
    assert body["status"] == "error"
    assert body["message"] == {"error": "nope"}
    assert mongo["bills"].find_one({"_id": ObjectId(bill_id)})["externalId"] == 0


@pytest.mark.gap
@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_billit_non_integer_success_body_is_unhandled(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-14 / TC-GAP-4 : int() on a non-integer body -> ValueError
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=1)
    billit_fake.add(billit_fake.POST, BILLIT_ORDERS_URL, json="not-an-int", status=200)
    with pytest.raises(ValueError):
        client.post(f"/api/bills/sendBillit/{bill_id}")


@pytest.mark.gap
@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_billit_non_json_error_body_is_unhandled(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-15 / TC-GAP-5 : response.json() on a non-JSON error body
    bill_id = insert_bill(mongo, order_number="2026-001", customer_id=1)
    billit_fake.add(
        billit_fake.POST,
        BILLIT_ORDERS_URL,
        body="Server Error",
        content_type="text/plain",
        status=500,
    )
    with pytest.raises(ValueError):
        client.post(f"/api/bills/sendBillit/{bill_id}")


# --- Credit-note Billit flow (TC-BILLIT-17 cnote, 19..22) --------------- #
@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_cnote_billit_success_order_type_credit_note(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-17 cnote / TC-BILLIT-21
    insert_bill(mongo, order_number="2026-001", customer_id=1)  # referenced invoice
    cnote_id = insert_cnote(
        mongo, order_number="C2026-001", customer_id=1, about_invoice_number="2026-001"
    )
    _register_orders_success(billit_fake)

    resp = client.post(f"/api/cnotes/sendBillit/{cnote_id}")
    assert resp.get_json()["status"] == "success"
    body = _orders_call_body(billit_fake)
    assert body["OrderType"] == "CreditNote"
    # TC-BILLIT-22 : cnote amounts are non-negative
    assert body["TotalExcl"] >= 0
    assert body["TotalIncl"] >= 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_cnote_billit_missing_about_invoice_number_is_warning(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-19
    cnote_id = insert_cnote(mongo, order_number="C2026-001", about_invoice_number="")
    resp = client.post(f"/api/cnotes/sendBillit/{cnote_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf")
def test_send_cnote_billit_referenced_invoice_not_local_is_warning(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-20 : referenced invoice absent from bills
    cnote_id = insert_cnote(
        mongo, order_number="C2026-001", about_invoice_number="2026-999"
    )
    resp = client.post(f"/api/cnotes/sendBillit/{cnote_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.usefixtures("fake_pdf", "seeded_customer")
def test_send_cnote_billit_referenced_invoice_local_but_unregistered_passes(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
) -> None:
    # TC-BILLIT-21 [ASSUMPTION] : local presence is enough; externalId not checked
    insert_bill(mongo, order_number="2026-001", customer_id=1, external_id=0)
    cnote_id = insert_cnote(
        mongo, order_number="C2026-001", customer_id=1, about_invoice_number="2026-001"
    )
    _register_orders_success(billit_fake)

    resp = client.post(f"/api/cnotes/sendBillit/{cnote_id}")
    assert resp.get_json()["status"] == "success"


# --- Billit delete (TC-BILLIT-DEL-3) ------------------------------------- #
def test_delete_order_2xx_non_true_body_is_failure(fake_env: dict[str, str]) -> None:
    # TC-BILLIT-DEL-3 : only b"true" is success
    import responses as _responses

    from controllers.billit import delete_order

    with _responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(rsps.DELETE, f"{fake_env['URL']}/orders/1", body="OK", status=200)
        result = delete_order(1)
    assert result is not None
    assert result["status"] == "error"


def test_delete_order_true_body_is_success(fake_env: dict[str, str]) -> None:
    # TC-BILLIT-DEL-1 (unit level)
    import responses as _responses

    from controllers.billit import delete_order

    with _responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(rsps.DELETE, f"{fake_env['URL']}/orders/1", body="true", status=200)
        result = delete_order(1)
    assert result is None  # None means success
