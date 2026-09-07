"""API-test helpers: direct DB seeding and small response conveniences."""

import json
from typing import TYPE_CHECKING, Any

from tests.helpers import DEFAULT_LINE

if TYPE_CHECKING:
    import mongomock
    from flask.testing import FlaskClient

CUSTOMERS_PATH = "/api/customers"
BILLS_PATH = "/api/bills"
CNOTES_PATH = "/api/cnotes"


def insert_bill(
    mongo: mongomock.Database,
    *,
    order_number: str = "2026-001",
    customer_id: int = 1,
    external_id: int = 0,
    peppol_status: int = -1,
    order_lines: list[dict[str, Any]] | None = None,
    ventilation_code: str = "2",
    order_title: str = "Chantier principal",
    order_date: str = "2026-09-06",
    about_invoice_number: str | None = None,
) -> str:
    """Insert a bill doc straight into the fake Mongo and return its _id string."""
    doc: dict[str, Any] = {
        "orderNumber": order_number,
        "customerId": customer_id,
        "externalId": external_id,
        "peppolDeliveryStatus": peppol_status,
        "orderLines": order_lines if order_lines is not None else [dict(DEFAULT_LINE)],
        "ventilationCode": ventilation_code,
        "orderTitle": order_title,
        "orderDate": order_date,
        "expiryDate": "2026-09-20",
        "deliveryDate": "2026-09-06",
    }
    if about_invoice_number is not None:
        doc["aboutInvoiceNumber"] = about_invoice_number
    return str(mongo["bills"].insert_one(doc).inserted_id)


def insert_cnote(
    mongo: mongomock.Database,
    *,
    order_number: str = "C2026-001",
    customer_id: int = 1,
    external_id: int = 0,
    peppol_status: int = -1,
    about_invoice_number: str = "2026-001",
    order_lines: list[dict[str, Any]] | None = None,
    ventilation_code: str = "2",
    order_title: str = "Note de crédit",
    order_date: str = "2026-09-06",
) -> str:
    """Insert a credit-note doc straight into the fake Mongo and return its id."""
    doc: dict[str, Any] = {
        "orderNumber": order_number,
        "customerId": customer_id,
        "externalId": external_id,
        "peppolDeliveryStatus": peppol_status,
        "aboutInvoiceNumber": about_invoice_number,
        "orderLines": order_lines if order_lines is not None else [dict(DEFAULT_LINE)],
        "ventilationCode": ventilation_code,
        "orderTitle": order_title,
        "orderDate": order_date,
        "expiryDate": "2026-09-20",
    }
    return str(mongo["cnotes"].insert_one(doc).inserted_id)


def post_bill(
    client: FlaskClient, payload: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    resp = client.post(BILLS_PATH, json=payload)
    return resp.status_code, resp.get_json()


def post_cnote(
    client: FlaskClient, payload: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    resp = client.post(CNOTES_PATH, json=payload)
    return resp.status_code, resp.get_json()


def get_customer_body(client: FlaskClient, customer_id: int) -> dict[str, Any]:
    """GET /api/customers/{id} returns a JSON *string* (not jsonify); parse it."""
    resp = client.get(f"{CUSTOMERS_PATH}/{customer_id}")
    assert resp.status_code == 200
    return json.loads(resp.data)
