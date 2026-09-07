"""TC-NFR-* : non-functional & cross-cutting requirements.

Some NFR cases are covered elsewhere (see cross-references); this file covers
the ones not already pinned: error-envelope shape, the Access lock, poller
non-blocking, full-collection listing, mtime reconnect, secret leakage,
no-auth, and tooling.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.api.helpers import insert_bill
from tests.helpers import make_customer_back

if TYPE_CHECKING:
    import mongomock
    import responses
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore

REPO_ROOT = Path(__file__).resolve().parents[2]
SECRET = "test-api-secret"  # mirrors FAKE_ENV["API_SECRET"] in tests/conftest.py


# --- Error envelope (TC-NFR-5) ------------------------------------------ #
def test_error_and_warning_envelopes_have_status_field(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
    mongo: mongomock.Database,
) -> None:
    # TC-NFR-5 : every non-success body includes a "status" field
    customer_store.seed(make_customer_back(id=1))
    insert_bill(mongo, order_number="2026-001")

    # error: duplicate order number
    dup = client.post(
        "/api/bills",
        json={
            "customerId": 1,
            "orderNumber": "2026-001",
            "orderDate": "2026-09-06",
            "expiryDate": "2026-09-20",
            "deliveryDate": "2026-09-06",
            "orderTitle": "T",
            "ventilationCode": "2",
            "orderLines": [
                {
                    "description": "d",
                    "quantity": 1,
                    "unitPriceExcl": 1.0,
                    "unit": "h",
                    "VATPercentage": 6.0,
                }
            ],
        },
    ).get_json()
    assert dup["status"] in ("error", "warning")

    # warning: undeletable bill delete
    undeletable_id = insert_bill(mongo, order_number="2026-002", peppol_status=1)
    warn = client.delete(f"/api/bills/{undeletable_id}").get_json()
    assert "status" in warn
    assert warn["status"] == "warning"


# --- Concurrency & performance (TC-NFR-6, 7, 8) ------------------------- #
def test_access_connector_serialises_through_one_lock() -> None:
    # TC-NFR-6 : the connector holds a single threading.Lock
    from database.access import SmartAccessConnector

    connector = SmartAccessConnector("/tmp/nonexistent.accdb", "jars")
    assert isinstance(connector.lock, type(threading.Lock()))


def test_send_peppol_does_not_block_request_handling(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    poller_spy: list[int],
    customer_store: FakeCustomerStore,
) -> None:
    # TC-NFR-7 : sendPeppol returns success; the poll is delegated to the
    # background (here recorded by the spy), not awaited inline.
    customer_store.seed(make_customer_back(id=1, vat_number="BE0"))
    bill_id = insert_bill(mongo, customer_id=1, external_id=42, peppol_status=-1)
    billit_fake.add(
        billit_fake.POST,
        "https://billit.test.local/v1/orders/commands/send",
        json={},
        status=201,
    )
    resp = client.post(f"/api/bills/sendPeppol/{bill_id}")
    assert resp.get_json()["status"] == "success"
    assert 42 in poller_spy


def test_listing_returns_the_full_collection(
    client: FlaskClient, customer_store: FakeCustomerStore, mongo: mongomock.Database
) -> None:
    # TC-NFR-8 : no pagination; all seeded docs are returned
    customer_store.seed(make_customer_back(id=1))
    for i in range(5):
        insert_bill(mongo, order_number=f"2026-{i:03d}", customer_id=1)
    assert len(client.get("/api/bills").get_json()) == 5


# --- Data integrity (TC-NFR-11) ------------------------------------------ #
def test_access_connector_reconnects_on_mtime_change(tmp_path: Path) -> None:
    # TC-NFR-11 / NFR-DI-3 : the connector reconnects when the .accdb mtime
    # advances. _connect is stubbed so no JVM is needed.
    from database.access import SmartAccessConnector

    db_file = tmp_path / "db.accdb"
    db_file.write_text("")

    class _FakeCursor:
        def execute(self, q: str, params: object = None) -> None:
            pass

        def fetchall(self) -> list:
            return []

        def fetchone(self) -> None:
            return None

        def close(self) -> None:
            pass

    class _FakeConn:
        def cursor(self) -> _FakeCursor:
            return _FakeCursor()

        def close(self) -> None:
            pass

    connects: list[int] = []
    connector = SmartAccessConnector(str(db_file), "jars", idle_timeout_sec=3600)
    connector._connect = lambda: (connects.append(1), _FakeConn())[1]  # type: ignore[method-assign]

    with connector.lock:
        connector.get_connection()
    assert len(connects) == 1

    # advance the file mtime and reconnect
    time.sleep(0.01)
    db_file.touch()
    with connector.lock:
        connector.get_connection()
    assert len(connects) == 2


# --- Security (TC-NFR-13, 14) -------------------------------------------- #
def test_api_secret_never_leaks_in_responses(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
    mongo: mongomock.Database,
) -> None:
    # TC-NFR-13
    customer_store.seed(make_customer_back(id=1))
    insert_bill(mongo, order_number="2026000001", customer_id=1)
    targets = [
        client.get("/api/customers").data,
        client.get("/api/bills").data,
        client.get(f"/api/bills/{mongo['bills'].find_one()['_id']}").data,
    ]
    for body in targets:
        assert SECRET.encode() not in body


@pytest.mark.gap
def test_no_auth_required_on_api(client: FlaskClient) -> None:
    # TC-NFR-14 / NFR-SEC-1 [GAP] : unauthenticated requests succeed
    assert client.get("/api/bills").status_code == 200


# --- Tooling (TC-NFR-16, 17) -------------------------------------------- #
def test_pytest_collects_from_repo_root() -> None:
    # TC-NFR-17 / NFR-MAINT-2 : the suite is discoverable/runs from repo root
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
