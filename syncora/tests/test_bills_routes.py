"""
Integration tests for the bills API  (routes/bills.py)
=======================================================

Every test sends a real HTTP request through Flask's test client so the full
stack is exercised:

    HTTP request → Blueprint route → controller → (mocked) model / external service

All I/O boundaries are patched at the *controller* import level so no real
MongoDB connection, Billit API call, or PDF generation happens.

Routes under test
─────────────────
  GET    /api/bills                        → get_bills
  POST   /api/bills                        → create_bill (new)
  GET    /api/bills/<id>                   → get_bill
  PUT    /api/bills/<id>                   → update_bill (= create_bill with db_id)
  DELETE /api/bills/<id>                   → delete_bill
  POST   /api/bills/sendPeppol/<id>        → send_bill_peppol
  POST   /api/bills/sendBillit/<id>        → send_bill_billit

PeppolDeliveryStatus constants  (constants/order_back.py)
──────────────────────────────
  -1  NOT_SENT
   0  UNKNOWN
   1  PENDING
   2  SENT
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Shared test data
# ──────────────────────────────────────────────────────────────────────────────

BILL_ID = "aabbccddeeff001122334455"

# A well-formed request body for POST /api/bills and PUT /api/bills/<id>
VALID_PAYLOAD = {
    "customerId": 42,
    "orderNumber": "2024-001",
    "orderDate": "2024-01-10",
    "expiryDate": "2024-02-10",
    "deliveryDate": "2024-01-15",
    "orderTitle": "Test invoice",
    "orderLines": [
        {
            "description": "Widget A",
            "quantity": 2,
            "unitPriceExcl": 100.0,
            "unit": "pcs",
            "VATPercentage": 21.0,
        }
    ],
    "ventilationCode": "V1",
}

# What the model layer returns for a single bill document
DB_BILL = {
    "_id": BILL_ID,
    "OrderID": 0,                   # not yet sent to Billit
    "CustomerId": 42,
    "OrderNumber": "2024-001",
    "OrderDate": "2024-01-10",
    "ExpiryDate": "2024-02-10",
    "DeliveryDate": "2024-01-15",
    "OrderTitle": "Test invoice",
    "OrderLines": [
        {
            "Description": "Widget A",
            "Quantity": 2,
            "UnitPriceExcl": 100.0,
            "Unit": "pcs",
            "VATPercentage": 21.0,
        }
    ],
    "VentilationCode": "V1",
    "PeppolDeliveryStatus": -1,     # NOT_SENT
}

# What get_customers_dict returns (keyed by customer id)
DB_CUSTOMER = {
    "Numero": 42,
    "Nom": "Dupont",
    "Prenom": "Jean",
    "Societe": "ACME SA",
    "Commentaire": "",
    "Adresse": "Rue de la Paix 1",
    "Codepostal": "1000",
    "Localite": "Bruxelles",
    "TVA": "BE0123456789",
    "Langue": "FR",
    "Titre": "M.",
}
CUSTOMERS_DICT = {42: DB_CUSTOMER}

# What convert_order_back_to_front returns (the "front" representation)
BILL_FRONT = {
    "customerId": 42,
    "orderNumber": "2024-001",
    "orderDate": "2024-01-10",
    "expiryDate": "2024-02-10",
    "deliveryDate": "2024-01-15",
    "orderTitle": "Test invoice",
    "orderLines": VALID_PAYLOAD["orderLines"],
    "ventilationCode": "V1",
    "billitSent": False,
    "peppolStatus": -1,
}


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Return a Flask test client. Created once for the entire module."""
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def body(response) -> dict | list:
    """Decode a Flask test-client response body as JSON."""
    return json.loads(response.data)


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/bills
# ══════════════════════════════════════════════════════════════════════════════

class TestGetBills:
    """Listing all bills: GET /api/bills"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        assert r.status_code == 200

    def test_content_type_is_json(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        assert r.content_type == "application/json"

    def test_response_is_array(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        assert isinstance(body(r), list)

    def test_item_has_required_keys(self, client):
        """Every item in the list must expose orderId, customerName, orderNumber, orderDate, orderTitle."""
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        item = body(r)[0]
        for key in ("orderId", "customerName", "orderNumber", "orderDate", "orderTitle"):
            assert key in item, f"Missing key: {key}"

    def test_item_values_are_correct(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        item = body(r)[0]
        assert item["orderId"] == BILL_ID
        assert item["orderNumber"] == "2024-001"
        assert item["orderDate"] == "2024-01-10"
        assert item["orderTitle"] == "Test invoice"

    def test_customer_name_includes_name_firstname_and_company(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[DB_BILL]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
        ):
            r = client.get("/api/bills")
        name = body(r)[0]["customerName"]
        assert "Dupont" in name
        assert "Jean" in name
        assert "ACME SA" in name

    def test_customer_name_no_company(self, client):
        """When Societe is None there should be no trailing ', None'."""
        bill = {**DB_BILL, "CustomerId": 7}
        customers = {7: {"Nom": "Martin", "Prenom": "Alice", "Societe": None}}
        with (
            patch("controllers.bills.model.get_bills", return_value=[bill]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            r = client.get("/api/bills")
        name = body(r)[0]["customerName"]
        assert name == "Martin Alice"
        assert "," not in name

    def test_customer_name_no_firstname(self, client):
        """When Prenom is None, the name must not have a trailing space."""
        bill = {**DB_BILL, "CustomerId": 8}
        customers = {8: {"Nom": "Leroy", "Prenom": None, "Societe": None}}
        with (
            patch("controllers.bills.model.get_bills", return_value=[bill]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            r = client.get("/api/bills")
        name = body(r)[0]["customerName"]
        assert name == "Leroy"

    def test_customer_name_only_company(self, client):
        """When both Nom and Prenom are None, only the company is shown."""
        bill = {**DB_BILL, "CustomerId": 9}
        customers = {9: {"Nom": None, "Prenom": None, "Societe": "BigCorp"}}
        with (
            patch("controllers.bills.model.get_bills", return_value=[bill]),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            r = client.get("/api/bills")
        name = body(r)[0]["customerName"]
        assert "BigCorp" in name

    def test_empty_database_returns_empty_list(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.mcust.get_customers_dict", return_value={}),
        ):
            r = client.get("/api/bills")
        assert body(r) == []

    def test_multiple_bills_are_all_returned(self, client):
        bills = [
            {**DB_BILL, "_id": "id1", "CustomerId": 1, "OrderNumber": "2024-001"},
            {**DB_BILL, "_id": "id2", "CustomerId": 1, "OrderNumber": "2024-002"},
            {**DB_BILL, "_id": "id3", "CustomerId": 1, "OrderNumber": "2024-003"},
        ]
        customers = {1: {"Nom": "X", "Prenom": "Y", "Societe": None}}
        with (
            patch("controllers.bills.model.get_bills", return_value=bills),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            r = client.get("/api/bills")
        assert len(body(r)) == 3

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_patch_method_not_allowed(self, client):
        r = client.patch("/api/bills")
        assert r.status_code == 405

    def test_delete_on_collection_not_allowed(self, client):
        r = client.delete("/api/bills")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/bills  (create)
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateBill:
    """Creating a new bill: POST /api/bills"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.insert_bill", return_value="new_id"),
        ):
            r = client.post("/api/bills", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.insert_bill", return_value="new_id"),
        ):
            r = client.post("/api/bills", json=VALID_PAYLOAD)
        assert body(r)["status"] == "success"

    def test_insert_bill_called_with_correct_arguments(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.insert_bill", return_value="new_id") as m,
        ):
            client.post("/api/bills", json=VALID_PAYLOAD)
        m.assert_called_once_with(
            customer_id=42,
            order_number="2024-001",
            order_date="2024-01-10",
            expiry_date="2024-02-10",
            delivery_date="2024-01-15",
            order_title="Test invoice",
            order_lines=VALID_PAYLOAD["orderLines"],
            ventilation_code="V1",
        )

    def test_missing_ventilation_code_defaults_to_empty_string(self, client):
        """ventilationCode is optional; absent → '' is forwarded to the model."""
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "ventilationCode"}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.insert_bill", return_value="x") as m,
        ):
            client.post("/api/bills", json=payload)
        _, kwargs = m.call_args
        assert kwargs["ventilation_code"] == ""

    # ── duplicate order number ────────────────────────────────────────────────

    def test_duplicate_order_number_returns_error_status(self, client):
        """If an order with the same OrderNumber already exists, creation is rejected."""
        with (
            patch("controllers.bills.model.get_bills", return_value=[{"_id": "other"}]),
            patch("controllers.bills.model.insert_bill") as m,
        ):
            r = client.post("/api/bills", json=VALID_PAYLOAD)
            m.assert_not_called()
        assert body(r)["status"] == "error"

    def test_duplicate_order_number_error_message_contains_order_number(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[{"_id": "other"}]),
            patch("controllers.bills.model.insert_bill"),
        ):
            r = client.post("/api/bills", json=VALID_PAYLOAD)
        assert "2024-001" in body(r)["message"]

    def test_insert_not_called_on_duplicate(self, client):
        with (
            patch("controllers.bills.model.get_bills", return_value=[{"_id": "other"}]),
            patch("controllers.bills.model.insert_bill") as m,
        ):
            client.post("/api/bills", json=VALID_PAYLOAD)
        m.assert_not_called()

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_put_on_collection_not_allowed(self, client):
        r = client.put("/api/bills", json=VALID_PAYLOAD)
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/bills/<bill_id>
# ══════════════════════════════════════════════════════════════════════════════

class TestGetBill:
    """Fetching a single bill: GET /api/bills/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200(self, client):
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller"),
        ):
            r = client.get(f"/api/bills/{BILL_ID}")
        assert r.status_code == 200

    def test_response_contains_order_data(self, client):
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller"),
        ):
            r = client.get(f"/api/bills/{BILL_ID}")
        data = body(r)
        assert data["orderNumber"] == "2024-001"
        assert data["customerId"] == 42
        assert data["billitSent"] is False

    def test_billit_sent_true_when_order_id_set(self, client):
        bill_with_billit = {**DB_BILL, "OrderID": 55}
        front_with_billit = {**BILL_FRONT, "billitSent": True}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_with_billit),
            patch("controllers.bills.convert_order_back_to_front", return_value=front_with_billit),
            patch("controllers.bills.PeppolStatusPoller"),
        ):
            r = client.get(f"/api/bills/{BILL_ID}")
        assert body(r)["billitSent"] is True

    def test_about_invoice_number_present_when_set(self, client):
        bill_with_ref = {**DB_BILL, "AboutInvoiceNumber": "2023-099"}
        front_with_ref = {**BILL_FRONT, "aboutInvoiceNumber": "2023-099"}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_with_ref),
            patch("controllers.bills.convert_order_back_to_front", return_value=front_with_ref),
            patch("controllers.bills.PeppolStatusPoller"),
        ):
            r = client.get(f"/api/bills/{BILL_ID}")
        assert body(r)["aboutInvoiceNumber"] == "2023-099"

    # ── Peppol-poller triggering logic ────────────────────────────────────────

    def test_peppol_status_not_sent_does_not_trigger_poller(self, client):
        """Status -1 (NOT_SENT): poller must NOT be called."""
        bill = {**DB_BILL, "PeppolDeliveryStatus": -1}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller") as mock_cls,
        ):
            client.get(f"/api/bills/{BILL_ID}")
        mock_cls.assert_not_called()

    def test_peppol_status_pending_triggers_poller(self, client):
        """Status 1 (PENDING): poller MUST be called with the bill's OrderID."""
        bill = {**DB_BILL, "PeppolDeliveryStatus": 1, "OrderID": 77}
        mock_instance = MagicMock()
        with (
            patch("controllers.bills.model.get_bill", return_value=bill),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller", return_value=mock_instance) as mock_cls,
        ):
            client.get(f"/api/bills/{BILL_ID}")
        mock_cls.assert_called_once()
        mock_instance.assert_called_once_with(77)

    def test_peppol_status_unknown_triggers_poller(self, client):
        """Status 0 (UNKNOWN): poller MUST be called."""
        bill = {**DB_BILL, "PeppolDeliveryStatus": 0, "OrderID": 88}
        mock_instance = MagicMock()
        with (
            patch("controllers.bills.model.get_bill", return_value=bill),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller", return_value=mock_instance),
        ):
            client.get(f"/api/bills/{BILL_ID}")
        mock_instance.assert_called_once_with(88)

    def test_peppol_status_sent_does_not_trigger_poller(self, client):
        """Status 2 (SENT): delivery is final, poller must NOT be called again."""
        bill = {**DB_BILL, "PeppolDeliveryStatus": 2, "OrderID": 99}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller") as mock_cls,
        ):
            client.get(f"/api/bills/{BILL_ID}")
        mock_cls.assert_not_called()

    def test_no_peppol_status_key_does_not_trigger_poller(self, client):
        """When the PeppolDeliveryStatus key is entirely absent, do not crash and do not poll."""
        bill = {k: v for k, v in DB_BILL.items() if k != "PeppolDeliveryStatus"}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill),
            patch("controllers.bills.convert_order_back_to_front", return_value=BILL_FRONT),
            patch("controllers.bills.PeppolStatusPoller") as mock_cls,
        ):
            r = client.get(f"/api/bills/{BILL_ID}")
        assert r.status_code == 200
        mock_cls.assert_not_called()

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_patch_on_bill_not_allowed(self, client):
        r = client.patch(f"/api/bills/{BILL_ID}")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/bills/<bill_id>  (update)
# ══════════════════════════════════════════════════════════════════════════════

class TestUpdateBill:
    """Updating an existing bill: PUT /api/bills/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        unlocked = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True),
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        unlocked = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True),
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        assert body(r)["status"] == "success"

    def test_response_contains_bill_id(self, client):
        """The response must echo the bill id that was updated."""
        unlocked = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True),
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        assert body(r)["id"] == BILL_ID

    def test_update_bill_called_with_correct_args(self, client):
        unlocked = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True) as m,
        ):
            client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        m.assert_called_once_with(
            bill_id=BILL_ID,
            customer_id=42,
            order_number="2024-001",
            order_date="2024-01-10",
            expiry_date="2024-02-10",
            delivery_date="2024-01-15",
            order_title="Test invoice",
            order_lines=VALID_PAYLOAD["orderLines"],
            ventilation_code="V1",
        )

    def test_updating_to_own_order_number_is_allowed(self, client):
        """
        When the only bill sharing the requested order-number is the bill being
        updated itself, the duplicate-check must pass.
        """
        existing = [{"_id": BILL_ID}]        # same id → not a real duplicate
        unlocked = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bills", return_value=existing),
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True) as m,
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        assert body(r)["status"] == "success"
        m.assert_called_once()

    # ── guard rails ───────────────────────────────────────────────────────────

    def test_locked_bill_returns_warning(self, client):
        """A bill that is already on Billit (OrderID != 0) must not be overwritten."""
        locked = {**DB_BILL, "OrderID": 99, "OrderNumber": "2024-001"}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=locked),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.model.update_bill") as m,
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_locked_bill_warning_contains_order_number(self, client):
        locked = {**DB_BILL, "OrderID": 99, "OrderNumber": "2024-001"}
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=locked),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.model.update_bill"),
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        assert "2024-001" in body(r)["message"]

    def test_duplicate_order_number_from_another_bill_returns_error(self, client):
        """Changing an order-number to one already used by a *different* bill is rejected."""
        existing = [{"_id": "some_other_id"}]
        with (
            patch("controllers.bills.model.get_bills", return_value=existing),
            patch("controllers.bills.model.update_bill") as m,
        ):
            r = client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
            m.assert_not_called()
        assert body(r)["status"] == "error"

    def test_update_not_called_on_duplicate(self, client):
        existing = [{"_id": "some_other_id"}]
        with (
            patch("controllers.bills.model.get_bills", return_value=existing),
            patch("controllers.bills.model.update_bill") as m,
        ):
            client.put(f"/api/bills/{BILL_ID}", json=VALID_PAYLOAD)
        m.assert_not_called()


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/bills/<bill_id>
# ══════════════════════════════════════════════════════════════════════════════

class TestDeleteBill:
    """Deleting a bill: DELETE /api/bills/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=True),
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=True),
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
        assert body(r)["status"] == "success"

    def test_delete_bill_model_is_called(self, client):
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=True) as m,
        ):
            client.delete(f"/api/bills/{BILL_ID}")
        m.assert_called_once_with(BILL_ID)

    # ── model failure ─────────────────────────────────────────────────────────

    def test_model_failure_returns_error_status(self, client):
        """When the model cannot delete (e.g. document already gone), return 'error'."""
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=False),
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
        assert body(r)["status"] == "error"

    # ── guard: Peppol-sent bills are undeletable ───────────────────────────────

    def test_peppol_sent_bill_returns_warning(self, client):
        """A bill whose Peppol status is not NOT_SENT (-1) must never be deleted."""
        peppol_sent = {**DB_BILL, "PeppolDeliveryStatus": 2}
        with (
            patch("controllers.bills.model.get_bill", return_value=peppol_sent),
            patch("controllers.bills.bill_undeletable", return_value=True),
            patch("controllers.bills.model.delete_bill") as m,
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_peppol_sent_warning_contains_bill_id(self, client):
        peppol_sent = {**DB_BILL, "PeppolDeliveryStatus": 2}
        with (
            patch("controllers.bills.model.get_bill", return_value=peppol_sent),
            patch("controllers.bills.bill_undeletable", return_value=True),
            patch("controllers.bills.model.delete_bill"),
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
        assert BILL_ID in body(r)["message"]

    def test_peppol_pending_bill_is_undeletable(self, client):
        peppol_pending = {**DB_BILL, "PeppolDeliveryStatus": 1}
        with (
            patch("controllers.bills.model.get_bill", return_value=peppol_pending),
            patch("controllers.bills.bill_undeletable", return_value=True),
            patch("controllers.bills.model.delete_bill") as m,
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_peppol_unknown_bill_is_undeletable(self, client):
        peppol_unknown = {**DB_BILL, "PeppolDeliveryStatus": 0}
        with (
            patch("controllers.bills.model.get_bill", return_value=peppol_unknown),
            patch("controllers.bills.bill_undeletable", return_value=True),
            patch("controllers.bills.model.delete_bill") as m,
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_not_sent_bill_can_be_deleted(self, client):
        """PeppolDeliveryStatus == -1 (NOT_SENT): deletion must succeed."""
        with (
            patch("controllers.bills.model.get_bill", return_value=DB_BILL),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=True) as m,
        ):
            r = client.delete(f"/api/bills/{BILL_ID}")
            m.assert_called_once()
        assert body(r)["status"] == "success"

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_post_on_single_bill_not_allowed(self, client):
        r = client.post(f"/api/bills/{BILL_ID}", json={})
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/bills/sendPeppol/<bill_id>
# ══════════════════════════════════════════════════════════════════════════════

class TestSendBillPeppol:
    """Sending a bill via Peppol: POST /api/bills/sendPeppol/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        bill_with_billit_id = {**DB_BILL, "OrderID": 999}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_with_billit_id),
            patch("controllers.bills.send_peppol", return_value={"status": "success"}),
        ):
            r = client.post(f"/api/bills/sendPeppol/{BILL_ID}")
        assert r.status_code == 200

    def test_send_peppol_called_with_billit_order_id(self, client):
        bill_with_billit_id = {**DB_BILL, "OrderID": 999}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_with_billit_id),
            patch("controllers.bills.send_peppol", return_value={"status": "success"}) as m,
        ):
            client.post(f"/api/bills/sendPeppol/{BILL_ID}")
        m.assert_called_once_with(999)

    # ── guard: bill must exist on Billit first ────────────────────────────────

    def test_order_id_zero_returns_warning(self, client):
        """OrderID == 0 means the bill hasn't been sent to Billit yet."""
        bill_no_billit = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_no_billit),
            patch("controllers.bills.send_peppol") as m,
        ):
            r = client.post(f"/api/bills/sendPeppol/{BILL_ID}")
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_order_id_zero_warning_mentions_bill_id(self, client):
        bill_no_billit = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_no_billit),
            patch("controllers.bills.send_peppol"),
        ):
            r = client.post(f"/api/bills/sendPeppol/{BILL_ID}")
        assert BILL_ID in body(r)["message"]

    def test_missing_order_id_key_returns_warning(self, client):
        """OrderID key entirely absent → treat as 0 (falsy) → warning."""
        bill_no_key = {k: v for k, v in DB_BILL.items() if k != "OrderID"}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_no_key),
            patch("controllers.bills.send_peppol") as m,
        ):
            r = client.post(f"/api/bills/sendPeppol/{BILL_ID}")
            m.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_send_peppol_not_called_when_no_billit_id(self, client):
        bill_no_billit = {**DB_BILL, "OrderID": 0}
        with (
            patch("controllers.bills.model.get_bill", return_value=bill_no_billit),
            patch("controllers.bills.send_peppol") as m,
        ):
            client.post(f"/api/bills/sendPeppol/{BILL_ID}")
        m.assert_not_called()

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_get_not_allowed(self, client):
        r = client.get(f"/api/bills/sendPeppol/{BILL_ID}")
        assert r.status_code == 405

    def test_delete_not_allowed(self, client):
        r = client.delete(f"/api/bills/sendPeppol/{BILL_ID}")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/bills/sendBillit/<bill_id>
# ══════════════════════════════════════════════════════════════════════════════

class TestSendBillBillit:
    """Sending a bill to Billit: POST /api/bills/sendBillit/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", return_value={"status": "success"}),
            patch("controllers.bills.model.set_order_id"),
        ):
            r = client.post(f"/api/bills/sendBillit/{BILL_ID}")
        assert r.status_code == 200

    def test_pdf_created_with_correct_order_and_customer(self, client):
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf") as m_pdf,
            patch("controllers.bills.send_billit", return_value={"status": "success"}),
            patch("controllers.bills.model.set_order_id"),
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
        m_pdf.assert_called_once_with(unlocked, DB_CUSTOMER)

    def test_send_billit_called_with_order_and_pdf_filename(self, client):
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", return_value={"status": "success"}) as m_send,
            patch("controllers.bills.model.set_order_id"),
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
        args, kwargs = m_send.call_args
        assert args[0] == unlocked
        assert args[1] == "/tmp/bill.pdf"

    def test_send_billit_receives_correct_customer_data(self, client):
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", return_value={"status": "success"}) as m_send,
            patch("controllers.bills.model.set_order_id"),
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
        _, kwargs = m_send.call_args
        assert kwargs["customer_data"] == DB_CUSTOMER

    def test_get_customers_dict_filtered_by_customer_id(self, client):
        """The controller must fetch only the bill's specific customer, not everyone."""
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT) as m_cust,
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", return_value={"status": "success"}),
            patch("controllers.bills.model.set_order_id"),
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
        # At least one call must carry the filter for this customer
        filter_calls = [
            kw for _, kw in (c for c in m_cust.call_args_list)
            if kw.get("filters", {}).get("Numero") == 42
        ]
        assert len(filter_calls) == 1

    def test_callback_stores_billit_order_id_in_db(self, client):
        """
        The lambda passed as callback to send_billit must call
        model.set_order_id(bill_id, <returned int>) when invoked.
        """
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        captured_cb = {}

        def fake_send_billit(order, filename, *, callback, customer_data):
            captured_cb["fn"] = callback
            return {"status": "success"}

        mock_response = MagicMock()
        mock_response.json.return_value = 12345

        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", side_effect=fake_send_billit),
            patch("controllers.bills.model.set_order_id") as m_set_id,
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
            captured_cb["fn"](mock_response)           # simulate Billit calling back

        m_set_id.assert_called_once_with(BILL_ID, 12345)

    def test_callback_casts_response_to_int(self, client):
        """response.json() may return a string; it must be cast to int."""
        unlocked = {**DB_BILL, "OrderID": 0, "CustomerId": 42}
        captured_cb = {}

        def fake_send_billit(order, filename, *, callback, customer_data):
            captured_cb["fn"] = callback
            return {"status": "success"}

        mock_response = MagicMock()
        mock_response.json.return_value = "99999"   # string, not int

        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=CUSTOMERS_DICT),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", side_effect=fake_send_billit),
            patch("controllers.bills.model.set_order_id") as m_set_id,
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
            captured_cb["fn"](mock_response)

        _, args, _ = m_set_id.mock_calls[0]
        assert isinstance(args[1], int)
        assert args[1] == 99999

    # ── guard: locked bill must be rejected ───────────────────────────────────

    def test_locked_bill_returns_warning(self, client):
        locked = {**DB_BILL, "OrderID": 77, "OrderNumber": "2024-001"}
        with (
            patch("controllers.bills.model.get_bill", return_value=locked),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.mcust.get_customers_dict") as m_cust,
            patch("controllers.bills.pdf.create_bill") as m_pdf,
            patch("controllers.bills.send_billit") as m_send,
        ):
            r = client.post(f"/api/bills/sendBillit/{BILL_ID}")
            m_cust.assert_not_called()
            m_pdf.assert_not_called()
            m_send.assert_not_called()
        assert body(r)["status"] == "warning"

    def test_locked_bill_warning_mentions_order_number(self, client):
        locked = {**DB_BILL, "OrderID": 77, "OrderNumber": "2024-001"}
        with (
            patch("controllers.bills.model.get_bill", return_value=locked),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.mcust.get_customers_dict"),
            patch("controllers.bills.pdf.create_bill"),
            patch("controllers.bills.send_billit"),
        ):
            r = client.post(f"/api/bills/sendBillit/{BILL_ID}")
        assert "2024-001" in body(r)["message"]

    def test_pdf_not_created_when_bill_is_locked(self, client):
        locked = {**DB_BILL, "OrderID": 77, "OrderNumber": "2024-001"}
        with (
            patch("controllers.bills.model.get_bill", return_value=locked),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.mcust.get_customers_dict"),
            patch("controllers.bills.pdf.create_bill") as m_pdf,
            patch("controllers.bills.send_billit"),
        ):
            client.post(f"/api/bills/sendBillit/{BILL_ID}")
        m_pdf.assert_not_called()

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_get_not_allowed(self, client):
        r = client.get(f"/api/bills/sendBillit/{BILL_ID}")
        assert r.status_code == 405

    def test_delete_not_allowed(self, client):
        r = client.delete(f"/api/bills/sendBillit/{BILL_ID}")
        assert r.status_code == 405

