"""
Unit tests for controllers/bills.py

Each function in the controller is tested in isolation by mocking all external
dependencies (database models, external API calls, PDF generation, Peppol poller, …).
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

# A minimal OrderFront-like dict that satisfies all json.get() calls in the
# controller under test.
SAMPLE_ORDER_FRONT = {
    "customerId": 42,
    "orderNumber": "2024-001",
    "orderDate": "2024-01-10",
    "expiryDate": "2024-02-10",
    "deliveryDate": "2024-01-15",
    "orderTitle": "Test invoice",
    "orderLines": [
        {
            "description": "Widget",
            "quantity": 2,
            "unitPriceExcl": 100.0,
            "unit": "pcs",
            "VATPercentage": 21.0,
        }
    ],
    "ventilationCode": "V1",
}

# A minimal OrderBack dict returned by the model layer.
SAMPLE_ORDER_BACK = {
    "_id": "abc123",
    "OrderID": 0,
    "CustomerId": 42,
    "OrderNumber": "2024-001",
    "OrderDate": "2024-01-10",
    "ExpiryDate": "2024-02-10",
    "DeliveryDate": "2024-01-15",
    "OrderTitle": "Test invoice",
    "OrderLines": [
        {
            "Description": "Widget",
            "Quantity": 2,
            "UnitPriceExcl": 100.0,
            "Unit": "pcs",
            "VATPercentage": 21.0,
        }
    ],
    "VentilationCode": "V1",
    "PeppolDeliveryStatus": -1,  # PEPPOL_DELIVERY_STATUS_NOT_SENT
}

# A sample customers dict as returned by mcust.get_customers_dict.
SAMPLE_CUSTOMERS = {
    42: {
        "Nom": "Dupont",
        "Prenom": "Jean",
        "Societe": "ACME",
        "Numero": 42,
        "Commentaire": "",
        "Adresse": "Rue de la Paix 1",
        "Codepostal": "1000",
        "Localite": "Bruxelles",
        "TVA": "BE0123456789",
        "Langue": "FR",
        "Titre": "M.",
    }
}


@pytest.fixture()
def app_ctx():
    """Provide a Flask application context so jsonify() works."""
    from app import create_app
    app = create_app()
    with app.app_context():
        yield app


# ---------------------------------------------------------------------------
# Tests for create_bill
# ---------------------------------------------------------------------------

class TestCreateBill:

    # ------------------------------------------------------------------
    # NEW bill (db_id == "")
    # ------------------------------------------------------------------

    def test_create_new_bill_success(self, app_ctx):
        """A new bill is inserted when no duplicate order-number exists."""
        with (
            patch("controllers.bills.model.get_bills", return_value=[]) as mock_get_bills,
            patch("controllers.bills.model.insert_bill", return_value="new_id") as mock_insert,
        ):
            from controllers.bills import create_bill

            response = create_bill(SAMPLE_ORDER_FRONT)
            data = json.loads(response.data)

            mock_get_bills.assert_called_once_with(condition={"OrderNumber": "2024-001"})
            mock_insert.assert_called_once_with(
                customer_id=42,
                order_number="2024-001",
                order_date="2024-01-10",
                expiry_date="2024-02-10",
                delivery_date="2024-01-15",
                order_title="Test invoice",
                order_lines=SAMPLE_ORDER_FRONT["orderLines"],
                ventilation_code="V1",
            )
            assert data["status"] == "success"

    def test_create_new_bill_duplicate_order_number_returns_error(self, app_ctx):
        """Creating a bill with a duplicate order-number (and no db_id) returns an error."""
        existing = [{"_id": "other_id"}]
        with (
            patch("controllers.bills.model.get_bills", return_value=existing),
            patch("controllers.bills.model.insert_bill") as mock_insert,
        ):
            from controllers.bills import create_bill

            response = create_bill(SAMPLE_ORDER_FRONT)
            data = json.loads(response.data)

            mock_insert.assert_not_called()
            assert data["status"] == "error"
            assert "2024-001" in data["message"]

    def test_create_new_bill_same_id_in_duplicate_set_is_allowed(self, app_ctx):
        """
        When the matching bill's _id equals db_id (update scenario), the duplicate
        check must pass and update_bill should be called.
        """
        existing = [{"_id": "abc123"}]
        order_data = {**SAMPLE_ORDER_BACK, "OrderID": 0}  # not locked

        with (
            patch("controllers.bills.model.get_bills", return_value=existing),
            patch("controllers.bills.model.get_bill", return_value=order_data),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True) as mock_update,
        ):
            from controllers.bills import create_bill

            response = create_bill(SAMPLE_ORDER_FRONT, db_id="abc123")
            data = json.loads(response.data)

            mock_update.assert_called_once()
            assert data["status"] == "success"

    # ------------------------------------------------------------------
    # UPDATE bill (db_id provided)
    # ------------------------------------------------------------------

    def test_update_existing_bill_success(self, app_ctx):
        """An existing, unlocked bill is updated correctly."""
        order_data = {**SAMPLE_ORDER_BACK, "OrderID": 0}

        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=order_data),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.model.update_bill", return_value=True) as mock_update,
        ):
            from controllers.bills import create_bill

            response = create_bill(SAMPLE_ORDER_FRONT, db_id="abc123")
            data = json.loads(response.data)

            mock_update.assert_called_once_with(
                bill_id="abc123",
                customer_id=42,
                order_number="2024-001",
                order_date="2024-01-10",
                expiry_date="2024-02-10",
                delivery_date="2024-01-15",
                order_title="Test invoice",
                order_lines=SAMPLE_ORDER_FRONT["orderLines"],
                ventilation_code="V1",
            )
            assert data["status"] == "success"
            assert data["id"] == "abc123"

    def test_update_locked_bill_returns_warning(self, app_ctx):
        """Trying to update a bill that is already locked returns a warning."""
        locked_order = {**SAMPLE_ORDER_BACK, "OrderID": 99, "OrderNumber": "2024-001"}

        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.get_bill", return_value=locked_order),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.model.update_bill") as mock_update,
        ):
            from controllers.bills import create_bill

            response = create_bill(SAMPLE_ORDER_FRONT, db_id="abc123")
            data = json.loads(response.data)

            mock_update.assert_not_called()
            assert data["status"] == "warning"

    def test_ventilation_code_defaults_to_empty_string(self, app_ctx):
        """ventilationCode defaults to '' when absent from the payload."""
        order_without_vc = {k: v for k, v in SAMPLE_ORDER_FRONT.items() if k != "ventilationCode"}

        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.model.insert_bill", return_value="new_id") as mock_insert,
        ):
            from controllers.bills import create_bill

            create_bill(order_without_vc)
            _, kwargs = mock_insert.call_args
            assert kwargs["ventilation_code"] == ""


# ---------------------------------------------------------------------------
# Tests for get_bill
# ---------------------------------------------------------------------------

class TestGetBill:

    def test_get_bill_no_peppol_status(self, app_ctx):
        """When there is no peppol status key, PeppolStatusPoller is NOT called."""
        order_back = {k: v for k, v in SAMPLE_ORDER_BACK.items() if k != "PeppolDeliveryStatus"}

        with (
            patch("controllers.bills.model.get_bill", return_value=order_back),
            patch("controllers.bills.convert_order_back_to_front", return_value={"ok": True}) as mock_conv,
            patch("controllers.bills.PeppolStatusPoller") as mock_poller,
        ):
            from controllers.bills import get_bill

            response = get_bill("abc123")
            data = json.loads(response.data)

            mock_poller.assert_not_called()
            mock_conv.assert_called_once_with(order_back)
            assert data["ok"] is True

    def test_get_bill_peppol_status_pending_triggers_poller(self, app_ctx):
        """When peppol status is PENDING, PeppolStatusPoller is invoked."""
        order_back = {**SAMPLE_ORDER_BACK, "PeppolDeliveryStatus": 1, "OrderID": 55}  # PENDING=1

        mock_poller_instance = MagicMock()
        with (
            patch("controllers.bills.model.get_bill", return_value=order_back),
            patch("controllers.bills.convert_order_back_to_front", return_value={}),
            patch("controllers.bills.PeppolStatusPoller", return_value=mock_poller_instance) as mock_poller_cls,
        ):
            from controllers.bills import get_bill

            get_bill("abc123")

            mock_poller_cls.assert_called_once()
            mock_poller_instance.assert_called_once_with(55)

    def test_get_bill_peppol_status_unknown_triggers_poller(self, app_ctx):
        """When peppol status is UNKNOWN (0), PeppolStatusPoller is invoked."""
        order_back = {**SAMPLE_ORDER_BACK, "PeppolDeliveryStatus": 0, "OrderID": 77}  # UNKNOWN=0

        mock_poller_instance = MagicMock()
        with (
            patch("controllers.bills.model.get_bill", return_value=order_back),
            patch("controllers.bills.convert_order_back_to_front", return_value={}),
            patch("controllers.bills.PeppolStatusPoller", return_value=mock_poller_instance),
        ):
            from controllers.bills import get_bill

            get_bill("abc123")

            mock_poller_instance.assert_called_once_with(77)

    def test_get_bill_peppol_status_sent_does_not_trigger_poller(self, app_ctx):
        """When peppol status is SENT (2), PeppolStatusPoller is NOT invoked."""
        order_back = {**SAMPLE_ORDER_BACK, "PeppolDeliveryStatus": 2, "OrderID": 88}  # SENT=2

        with (
            patch("controllers.bills.model.get_bill", return_value=order_back),
            patch("controllers.bills.convert_order_back_to_front", return_value={}),
            patch("controllers.bills.PeppolStatusPoller") as mock_poller_cls,
        ):
            from controllers.bills import get_bill

            get_bill("abc123")

            mock_poller_cls.assert_not_called()

    def test_get_bill_returns_converted_order(self, app_ctx):
        """The JSON response contains the data produced by convert_order_back_to_front."""
        converted = {"orderNumber": "2024-001", "customerId": 42}

        with (
            patch("controllers.bills.model.get_bill", return_value=SAMPLE_ORDER_BACK),
            patch("controllers.bills.convert_order_back_to_front", return_value=converted),
            patch("controllers.bills.PeppolStatusPoller"),
        ):
            from controllers.bills import get_bill

            response = get_bill("abc123")
            data = json.loads(response.data)

            assert data["orderNumber"] == "2024-001"
            assert data["customerId"] == 42


# ---------------------------------------------------------------------------
# Tests for get_bills
# ---------------------------------------------------------------------------

class TestGetBills:

    def test_get_bills_returns_list(self, app_ctx):
        """get_bills assembles the list of OrderFrontShort dicts and returns them."""
        bills = [
            {
                "_id": "id1",
                "CustomerId": 42,
                "OrderNumber": "2024-001",
                "OrderDate": "2024-01-10",
                "OrderTitle": "Title 1",
            }
        ]
        customers = {
            42: {"Nom": "Dupont", "Prenom": "Jean", "Societe": "ACME"}
        }

        with (
            patch("controllers.bills.model.get_bills", return_value=bills),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            from controllers.bills import get_bills

            response = get_bills()
            data = json.loads(response.data)

            assert len(data) == 1
            assert data[0]["orderId"] == "id1"
            assert data[0]["orderNumber"] == "2024-001"
            assert "Dupont" in data[0]["customerName"]
            assert "Jean" in data[0]["customerName"]
            assert "ACME" in data[0]["customerName"]

    def test_get_bills_customer_name_without_company(self, app_ctx):
        """When Societe is absent, customer_name has no trailing comma."""
        bills = [
            {
                "_id": "id2",
                "CustomerId": 10,
                "OrderNumber": "2024-002",
                "OrderDate": "2024-01-11",
                "OrderTitle": "Title 2",
            }
        ]
        customers = {10: {"Nom": "Smith", "Prenom": "John", "Societe": None}}

        with (
            patch("controllers.bills.model.get_bills", return_value=bills),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            from controllers.bills import get_bills

            response = get_bills()
            data = json.loads(response.data)

            assert data[0]["customerName"] == "Smith John"
            assert "," not in data[0]["customerName"]

    def test_get_bills_empty_list(self, app_ctx):
        """When there are no bills, an empty list is returned."""
        with (
            patch("controllers.bills.model.get_bills", return_value=[]),
            patch("controllers.bills.mcust.get_customers_dict", return_value={}),
        ):
            from controllers.bills import get_bills

            response = get_bills()
            data = json.loads(response.data)

            assert data == []

    def test_get_bills_customer_name_only_company(self, app_ctx):
        """When Nom and Prenom are None, only the company name is shown."""
        bills = [
            {
                "_id": "id3",
                "CustomerId": 7,
                "OrderNumber": "2024-003",
                "OrderDate": "2024-01-12",
                "OrderTitle": "Title 3",
            }
        ]
        customers = {7: {"Nom": None, "Prenom": None, "Societe": "BigCorp"}}

        with (
            patch("controllers.bills.model.get_bills", return_value=bills),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customers),
        ):
            from controllers.bills import get_bills

            response = get_bills()
            data = json.loads(response.data)

            assert data[0]["customerName"] == ", BigCorp"


# ---------------------------------------------------------------------------
# Tests for update_bill
# ---------------------------------------------------------------------------

class TestUpdateBill:

    def test_update_bill_delegates_to_create_bill(self, app_ctx):
        """update_bill is a thin wrapper around create_bill with db_id set."""
        with patch("controllers.bills.create_bill", return_value=MagicMock()) as mock_create:
            from controllers.bills import update_bill

            update_bill("abc123", SAMPLE_ORDER_FRONT)
            mock_create.assert_called_once_with(SAMPLE_ORDER_FRONT, db_id="abc123")


# ---------------------------------------------------------------------------
# Tests for delete_bill
# ---------------------------------------------------------------------------

class TestDeleteBill:

    def test_delete_bill_success(self, app_ctx):
        """A deletable bill is deleted and a success response is returned."""
        with (
            patch("controllers.bills.model.get_bill", return_value=SAMPLE_ORDER_BACK),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=True),
        ):
            from controllers.bills import delete_bill

            response = delete_bill("abc123")
            data = json.loads(response.data)

            assert data["status"] == "success"

    def test_delete_bill_not_found_in_db(self, app_ctx):
        """When delete_bill model returns False, the status is error."""
        with (
            patch("controllers.bills.model.get_bill", return_value=SAMPLE_ORDER_BACK),
            patch("controllers.bills.bill_undeletable", return_value=False),
            patch("controllers.bills.model.delete_bill", return_value=False),
        ):
            from controllers.bills import delete_bill

            response = delete_bill("abc123")
            data = json.loads(response.data)

            assert data["status"] == "error"

    def test_delete_bill_undeletable_returns_warning(self, app_ctx):
        """A bill that has been sent to Peppol cannot be deleted."""
        peppol_sent_order = {**SAMPLE_ORDER_BACK, "PeppolDeliveryStatus": 2}

        with (
            patch("controllers.bills.model.get_bill", return_value=peppol_sent_order),
            patch("controllers.bills.bill_undeletable", return_value=True),
            patch("controllers.bills.model.delete_bill") as mock_delete,
        ):
            from controllers.bills import delete_bill

            response = delete_bill("abc123")
            data = json.loads(response.data)

            mock_delete.assert_not_called()
            assert data["status"] == "warning"
            assert "abc123" in data["message"]


# ---------------------------------------------------------------------------
# Tests for send_bill_peppol
# ---------------------------------------------------------------------------

class TestSendBillPeppol:

    def test_send_bill_peppol_success(self, app_ctx):
        """When OrderID is present, send_peppol is called with that ID."""
        order_with_id = {**SAMPLE_ORDER_BACK, "OrderID": 999}
        mock_peppol_response = MagicMock()

        with (
            patch("controllers.bills.model.get_bill", return_value=order_with_id),
            patch("controllers.bills.send_peppol", return_value=mock_peppol_response) as mock_send,
        ):
            from controllers.bills import send_bill_peppol

            result = send_bill_peppol("abc123")

            mock_send.assert_called_once_with(999)
            assert result is mock_peppol_response

    def test_send_bill_peppol_missing_order_id_returns_warning(self, app_ctx):
        """When the bill has no Billit OrderID, a warning is returned."""
        order_without_id = {**SAMPLE_ORDER_BACK, "OrderID": 0}

        with (
            patch("controllers.bills.model.get_bill", return_value=order_without_id),
            patch("controllers.bills.send_peppol") as mock_send,
        ):
            from controllers.bills import send_bill_peppol

            response = send_bill_peppol("abc123")
            data = json.loads(response.data)

            mock_send.assert_not_called()
            assert data["status"] == "warning"
            assert "abc123" in data["message"]

    def test_send_bill_peppol_order_id_absent_key_returns_warning(self, app_ctx):
        """When OrderID key is completely absent, a warning is returned."""
        order_no_key = {k: v for k, v in SAMPLE_ORDER_BACK.items() if k != "OrderID"}

        with (
            patch("controllers.bills.model.get_bill", return_value=order_no_key),
            patch("controllers.bills.send_peppol") as mock_send,
        ):
            from controllers.bills import send_bill_peppol

            response = send_bill_peppol("abc123")
            data = json.loads(response.data)

            mock_send.assert_not_called()
            assert data["status"] == "warning"


# ---------------------------------------------------------------------------
# Tests for send_bill_billit
# ---------------------------------------------------------------------------

class TestSendBillBillit:

    def test_send_bill_billit_locked_returns_warning(self, app_ctx):
        """A locked bill cannot be sent to Billit again."""
        locked_order = {**SAMPLE_ORDER_BACK, "OrderID": 99, "OrderNumber": "2024-001"}

        with (
            patch("controllers.bills.model.get_bill", return_value=locked_order),
            patch("controllers.bills.bill_locked", return_value=True),
            patch("controllers.bills.mcust.get_customers_dict") as mock_cust,
            patch("controllers.bills.pdf.create_bill") as mock_pdf,
            patch("controllers.bills.send_billit") as mock_send,
        ):
            from controllers.bills import send_bill_billit

            response = send_bill_billit("abc123")
            data = json.loads(response.data)

            mock_cust.assert_not_called()
            mock_pdf.assert_not_called()
            mock_send.assert_not_called()
            assert data["status"] == "warning"
            assert "2024-001" in data["message"]

    def test_send_bill_billit_success(self, app_ctx):
        """An unlocked bill generates a PDF and sends it to Billit."""
        unlocked_order = {**SAMPLE_ORDER_BACK, "OrderID": 0, "CustomerId": 42}
        mock_billit_response = MagicMock()

        customer_dict = {42: SAMPLE_CUSTOMERS[42]}

        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked_order),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customer_dict),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf") as mock_pdf,
            patch("controllers.bills.send_billit", return_value=mock_billit_response) as mock_send,
            patch("controllers.bills.model.set_order_id"),
        ):
            from controllers.bills import send_bill_billit

            result = send_bill_billit("abc123")

            mock_pdf.assert_called_once_with(unlocked_order, SAMPLE_CUSTOMERS[42])
            mock_send.assert_called_once()
            # Check positional arguments: (order_data, filename, callback, customer_data)
            send_args, send_kwargs = mock_send.call_args
            assert send_args[0] == unlocked_order
            assert send_args[1] == "/tmp/bill.pdf"
            assert send_kwargs["customer_data"] == SAMPLE_CUSTOMERS[42]
            assert result is mock_billit_response

    def test_send_bill_billit_callback_calls_set_order_id(self, app_ctx):
        """The callback passed to send_billit correctly calls model.set_order_id."""
        unlocked_order = {**SAMPLE_ORDER_BACK, "OrderID": 0, "CustomerId": 42}
        customer_dict = {42: SAMPLE_CUSTOMERS[42]}

        captured_callback = {}

        def capture_send_billit(order, filename, *, callback, customer_data):
            captured_callback["fn"] = callback
            return MagicMock()

        mock_response = MagicMock()
        mock_response.json.return_value = 12345

        with (
            patch("controllers.bills.model.get_bill", return_value=unlocked_order),
            patch("controllers.bills.bill_locked", return_value=False),
            patch("controllers.bills.mcust.get_customers_dict", return_value=customer_dict),
            patch("controllers.bills.pdf.create_bill", return_value="/tmp/bill.pdf"),
            patch("controllers.bills.send_billit", side_effect=capture_send_billit),
            patch("controllers.bills.model.set_order_id") as mock_set_id,
        ):
            from controllers.bills import send_bill_billit

            send_bill_billit("abc123")

            # Fire the callback as send_billit would.
            captured_callback["fn"](mock_response)
            mock_set_id.assert_called_once_with("abc123", 12345)

