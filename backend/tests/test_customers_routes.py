"""
Integration tests for the customers API  (routes/customers.py)
==============================================================

Every test sends a real HTTP request through Flask's test client so the full
stack is exercised:

    HTTP request → Blueprint route → controller → (mocked) model

All database I/O is patched at the *controller* import level.

Routes under test
─────────────────
  GET    /api/customers              → get_customers   (list)
  POST   /api/customers              → create_customer
  GET    /api/customers/<id>         → get_customer    (single)
  PUT    /api/customers/<id>         → update_customer
  DELETE /api/customers/<id>         → delete_customer

Helper functions under test (pure, no mocking needed)
─────────────────────────────────────────────────────
  detect_phones  / detect_mobiles / detect_emails
  is_old_db_comment
  get_customer_street / get_customer_street_number  (in model)

Bugs detected by the test suite
────────────────────────────────
  BUG-1  create_customer / update_customer crash with AttributeError when
         `street` or `number` is None because .strip() is called on None.
  BUG-2  delete_customer always returns "success" even when the customer
         does not exist — no existence-check / error path.
  BUG-3  detect_phones pattern r'0\\d{8}' (9 total digits) is a strict
         sub-string of a mobile number (10 digits), so a mobile like
         0491234567 is also matched by the fixed-line pattern → duplicate
         in the combined phones+mobiles list returned by get_customers.
  BUG-4  is_old_db_comment returns True for None (correct) but returns
         False for a properly formatted new-style "##...##" comment —
         i.e. the return value is inverted: it should be True for OLD
         style (no ## markers) and False for NEW style (## markers).
"""

import json
from unittest.mock import MagicMock, patch, call

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def body(response) -> dict | list:
    return json.loads(response.data)


# ──────────────────────────────────────────────────────────────────────────────
# Shared test data
# ──────────────────────────────────────────────────────────────────────────────

CUSTOMER_ID = 7

# Row tuple returned by model.get_customers for GET /api/customers (8 fields)
# Numero, Nom, Prenom, Societe, Commentaire, Codepostal, Localite, TVA
CUSTOMER_ROW_LIST = (
    CUSTOMER_ID,
    "Dupont",
    "Jean",
    "ACME SA",
    "Tel: 02/123 45 67 email: jean@acme.be",
    "1000",
    "Bruxelles",
    "BE0123456789",
)

# Row tuple returned by model.get_customers for GET /api/customers/<id> (12 fields)
# Numero, Nom, Prenom, Societe, Commentaire, Adresse, Codepostal, Localite, TVA, Langue, NomArchitecte, Titre
CUSTOMER_ROW_DETAIL = (
    CUSTOMER_ID,
    "Dupont",
    "Jean",
    "ACME SA",
    "Some comment",
    "Rue de la Paix , 1",
    "1000",
    "Bruxelles",
    "BE0123456789",
    "FR",
    "Arch. Martin",
    "M.",
)

# A well-formed POST/PUT request body
VALID_PAYLOAD = {
    "name": "Dupont",
    "surname": "Jean",
    "company": "ACME SA",
    "comment": "Some comment",
    "street": "Rue de la Paix",
    "number": "1",
    "postal_code": "1000",
    "city": "Bruxelles",
    "vat_number": "BE0123456789",
    "language": "FR",
    "architect_name": "Arch. Martin",
    "salutation": "M.",
}


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/customers
# ══════════════════════════════════════════════════════════════════════════════

class TestGetCustomers:
    """Listing all customers: GET /api/customers"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        assert r.status_code == 200

    def test_content_type_is_json(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        assert r.content_type == "application/json"

    def test_response_is_array(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        assert isinstance(body(r), list)

    def test_item_has_required_keys(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        item = body(r)[0]
        for key in ("id", "name", "surname", "company", "phones", "hasEmail", "hasVAT", "postal_code", "city"):
            assert key in item, f"Missing key: {key}"

    def test_item_values_are_correct(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        item = body(r)[0]
        assert item["id"] == CUSTOMER_ID
        assert item["name"] == "Dupont"
        assert item["surname"] == "Jean"
        assert item["company"] == "ACME SA"
        assert item["postal_code"] == "1000"
        assert item["city"] == "Bruxelles"

    def test_has_vat_true_when_vat_number_set(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasVAT"] is True

    def test_has_vat_false_when_vat_number_is_none(self, client):
        row = CUSTOMER_ROW_LIST[:7] + (None,)
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasVAT"] is False

    def test_has_vat_false_when_vat_number_is_empty_string(self, client):
        row = CUSTOMER_ROW_LIST[:7] + ("",)
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasVAT"] is False

    def test_has_email_true_when_email_in_comment(self, client):
        """The comment "jean@acme.be" should yield hasEmail=True."""
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_LIST]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasEmail"] is True

    def test_has_email_false_when_no_email_in_comment(self, client):
        row = (CUSTOMER_ID, "X", "Y", "Z", "no email here", "1000", "City", "BE0")
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasEmail"] is False

    def test_has_email_false_when_comment_is_none(self, client):
        row = CUSTOMER_ROW_LIST[:4] + (None,) + CUSTOMER_ROW_LIST[5:]
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        assert body(r)[0]["hasEmail"] is False

    def test_phones_detected_from_comment(self, client):
        """A landline number in the comment must appear in the phones list."""
        row = (CUSTOMER_ID, "X", "Y", "Z", "Tel: 02/123 45 67", "1000", "City", None)
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        phones = body(r)[0]["phones"]
        assert len(phones) > 0
        assert any("021234567" in p for p in phones)

    def test_phones_empty_when_comment_is_none(self, client):
        row = CUSTOMER_ROW_LIST[:4] + (None,) + CUSTOMER_ROW_LIST[5:]
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        assert body(r)[0]["phones"] == []

    def test_empty_database_returns_empty_list(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[]):
            r = client.get("/api/customers")
        assert body(r) == []

    def test_multiple_customers_all_returned(self, client):
        rows = [
            (1, "A", "B", "C", None, "1000", "City", None),
            (2, "D", "E", "F", None, "2000", "Town", "BE1"),
            (3, "G", "H", "I", None, "3000", "Village", None),
        ]
        with patch("controllers.customers.model.get_customers", return_value=rows):
            r = client.get("/api/customers")
        assert len(body(r)) == 3

    # ── BUG-3: mobile number must not appear in fixed-line phones list ─────────

    def test_bug3_mobile_not_duplicated_in_phones_list(self, client):
        """
        BUG-3: pattern r'0\\d{8}' (9 digits) matches the first 9 digits of a
        10-digit mobile (0491234567), so detect_phones() incorrectly picks it
        up as a landline. The combined phones list therefore contains the same
        number twice.
        """
        mobile = "0491234567"
        row = (CUSTOMER_ID, "X", "Y", "Z", mobile, "1000", "City", None)
        with patch("controllers.customers.model.get_customers", return_value=[row]):
            r = client.get("/api/customers")
        phones = body(r)[0]["phones"]
        # The mobile should appear exactly once (only from detect_mobiles)
        # BUG: detect_phones ALSO matches the first 9 digits → count > 1
        assert phones.count(mobile) == 1, (
            "BUG-3: mobile number is duplicated in the phones list because "
            "detect_phones matches a subset of the mobile number"
        )

    # ── wrong methods ─────────────────────────────────────────────────────────

    def test_patch_not_allowed(self, client):
        r = client.patch("/api/customers")
        assert r.status_code == 405

    def test_delete_not_allowed(self, client):
        r = client.delete("/api/customers")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/customers
# ══════════════════════════════════════════════════════════════════════════════

class TestCreateCustomer:
    """Creating a new customer: POST /api/customers"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=10),
            patch("controllers.customers.model.create_customer", return_value=11),
        ):
            r = client.post("/api/customers", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=10),
            patch("controllers.customers.model.create_customer", return_value=11),
        ):
            r = client.post("/api/customers", json=VALID_PAYLOAD)
        assert body(r)["status"] == "success"

    def test_response_contains_new_id(self, client):
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=10),
            patch("controllers.customers.model.create_customer", return_value=11),
        ):
            r = client.post("/api/customers", json=VALID_PAYLOAD)
        assert body(r)["id"] == 11

    def test_address_formatted_correctly(self, client):
        """street and number must be joined as 'street , number' in Adresse."""
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=0),
            patch("controllers.customers.model.create_customer", return_value=1) as m,
        ):
            client.post("/api/customers", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        customer_back = args[0]
        assert customer_back["Adresse"] == "Rue de la Paix , 1"

    def test_all_fields_forwarded_to_model(self, client):
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=0),
            patch("controllers.customers.model.create_customer", return_value=1) as m,
        ):
            client.post("/api/customers", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        cb = args[0]
        assert cb["Nom"] == "Dupont"
        assert cb["Prenom"] == "Jean"
        assert cb["Societe"] == "ACME SA"
        assert cb["Commentaire"] == "Some comment"
        assert cb["Codepostal"] == "1000"
        assert cb["Localite"] == "Bruxelles"
        assert cb["TVA"] == "BE0123456789"
        assert cb["Langue"] == "FR"
        assert cb["NomArchitecte"] == "Arch. Martin"
        assert cb["Titre"] == "M."

    def test_street_and_number_are_stripped(self, client):
        """Leading/trailing whitespace on street and number must be removed."""
        payload = {**VALID_PAYLOAD, "street": "  Rue Test  ", "number": "  42  "}
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=0),
            patch("controllers.customers.model.create_customer", return_value=1) as m,
        ):
            client.post("/api/customers", json=payload)
        _, args, _ = m.mock_calls[0]
        assert args[0]["Adresse"] == "Rue Test , 42"

    def test_numero_is_last_id_plus_one(self, client):
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=99),
            patch("controllers.customers.model.create_customer", return_value=100) as m,
        ):
            client.post("/api/customers", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        assert args[0]["Numero"] == 100

    # ── BUG-1: crash when street or number is None ────────────────────────────

    def test_bug1_create_crashes_when_street_is_none(self, client):
        """
        BUG-1: json.get('street').strip() raises AttributeError when street
        is absent from the payload (returns None).
        """
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "street"}
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=0),
            patch("controllers.customers.model.create_customer", return_value=1),
        ):
            r = client.post("/api/customers", json=payload)
        # Should return a graceful error response, not an unhandled 500
        assert r.status_code != 500, (
            "BUG-1: AttributeError raised because .strip() is called on None "
            "when 'street' is missing from the payload"
        )

    def test_bug1_create_crashes_when_number_is_none(self, client):
        """
        BUG-1: same crash when 'number' is absent.
        """
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "number"}
        with (
            patch("controllers.customers.model.get_last_customer_id", return_value=0),
            patch("controllers.customers.model.create_customer", return_value=1),
        ):
            r = client.post("/api/customers", json=payload)
        assert r.status_code != 500, (
            "BUG-1: AttributeError raised because .strip() is called on None "
            "when 'number' is missing from the payload"
        )

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_put_on_collection_not_allowed(self, client):
        r = client.put("/api/customers", json=VALID_PAYLOAD)
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/customers/<id>
# ══════════════════════════════════════════════════════════════════════════════

class TestGetCustomer:
    """Fetching a single customer: GET /api/customers/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        assert r.status_code == 200

    def test_response_contains_all_fields(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        data = body(r)
        for key in ("id", "name", "surname", "company", "comment",
                    "street", "number", "postal_code", "city",
                    "vat_number", "language", "salutation"):
            assert key in data, f"Missing key: {key}"

    def test_response_values_are_correct(self, client):
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        data = body(r)
        assert data["id"] == CUSTOMER_ID
        assert data["name"] == "Dupont"
        assert data["surname"] == "Jean"
        assert data["company"] == "ACME SA"
        assert data["comment"] == "Some comment"
        assert data["postal_code"] == "1000"
        assert data["city"] == "Bruxelles"
        assert data["vat_number"] == "BE0123456789"
        assert data["language"] == "FR"
        assert data["salutation"] == "M."

    def test_address_split_into_street_and_number(self, client):
        """Address 'Rue de la Paix , 1' must be split into street and number."""
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        data = body(r)
        assert data["street"] == "Rue de la Paix"
        assert data["number"] == "1"

    def test_address_with_number_containing_comma(self, client):
        """Address 'Street , 10, box 3' — everything after first comma is the number."""
        row = list(CUSTOMER_ROW_DETAIL)
        row[5] = "Main Street , 10, box 3"
        with patch("controllers.customers.model.get_customers", return_value=[tuple(row)]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        data = body(r)
        assert data["street"] == "Main Street"
        assert "10" in data["number"]

    def test_address_no_comma_returns_empty_number(self, client):
        """If there is no comma in the address, number should be empty."""
        row = list(CUSTOMER_ROW_DETAIL)
        row[5] = "NoCommaAddress"
        with patch("controllers.customers.model.get_customers", return_value=[tuple(row)]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        data = body(r)
        assert data["street"] == "NoCommaAddress"
        assert data["number"] == ""

    def test_model_called_with_correct_filter(self, client):
        """get_customers must be called with a filter for the requested customer id."""
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]) as m:
            client.get(f"/api/customers/{CUSTOMER_ID}")
        _, kwargs = m.call_args
        assert kwargs.get("filters", {}).get("Numero") == CUSTOMER_ID

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_patch_not_allowed(self, client):
        r = client.patch(f"/api/customers/{CUSTOMER_ID}")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/customers/<id>
# ══════════════════════════════════════════════════════════════════════════════

class TestUpdateCustomer:
    """Updating a customer: PUT /api/customers/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        with patch("controllers.customers.model.update_customer"):
            r = client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        with patch("controllers.customers.model.update_customer"):
            r = client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        assert body(r)["status"] == "success"

    def test_response_contains_customer_id(self, client):
        """The response must echo back the id of the updated customer."""
        with patch("controllers.customers.model.update_customer"):
            r = client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        assert body(r)["id"] == CUSTOMER_ID

    def test_model_called_with_correct_customer_id(self, client):
        with patch("controllers.customers.model.update_customer") as m:
            client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        args, _ = m.call_args
        assert args[0] == CUSTOMER_ID

    def test_address_formatted_correctly(self, client):
        """street and number must be joined as 'street , number' in Adresse."""
        with patch("controllers.customers.model.update_customer") as m:
            client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        assert args[1]["Adresse"] == "Rue de la Paix , 1"

    def test_all_fields_forwarded_to_model(self, client):
        with patch("controllers.customers.model.update_customer") as m:
            client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        cb = args[1]
        assert cb["Nom"] == "Dupont"
        assert cb["Prenom"] == "Jean"
        assert cb["Societe"] == "ACME SA"
        assert cb["TVA"] == "BE0123456789"
        assert cb["Langue"] == "FR"
        assert cb["Titre"] == "M."

    def test_street_and_number_are_stripped(self, client):
        payload = {**VALID_PAYLOAD, "street": "  Avenue Test  ", "number": "  7  "}
        with patch("controllers.customers.model.update_customer") as m:
            client.put(f"/api/customers/{CUSTOMER_ID}", json=payload)
        _, args, _ = m.mock_calls[0]
        assert args[1]["Adresse"] == "Avenue Test , 7"

    def test_numero_not_included_in_update_payload(self, client):
        """The update CustomerBack must NOT contain Numero (would overwrite PK)."""
        with patch("controllers.customers.model.update_customer") as m:
            client.put(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        _, args, _ = m.mock_calls[0]
        assert "Numero" not in args[1]

    # ── BUG-1: crash when street or number is None ────────────────────────────

    def test_bug1_update_crashes_when_street_is_none(self, client):
        """
        BUG-1: json.get('street').strip() raises AttributeError when street
        is absent from the payload.
        """
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "street"}
        with patch("controllers.customers.model.update_customer"):
            r = client.put(f"/api/customers/{CUSTOMER_ID}", json=payload)
        assert r.status_code != 500, (
            "BUG-1: AttributeError raised because .strip() is called on None "
            "when 'street' is missing from the payload"
        )

    def test_bug1_update_crashes_when_number_is_none(self, client):
        """
        BUG-1: json.get('number').strip() raises AttributeError when number
        is absent from the payload.
        """
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "number"}
        with patch("controllers.customers.model.update_customer"):
            r = client.put(f"/api/customers/{CUSTOMER_ID}", json=payload)
        assert r.status_code != 500, (
            "BUG-1: AttributeError raised because .strip() is called on None "
            "when 'number' is missing from the payload"
        )

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_post_not_allowed(self, client):
        r = client.post(f"/api/customers/{CUSTOMER_ID}", json=VALID_PAYLOAD)
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/customers/<id>
# ══════════════════════════════════════════════════════════════════════════════

class TestDeleteCustomer:
    """Deleting a customer: DELETE /api/customers/<id>"""

    # ── happy path ────────────────────────────────────────────────────────────

    def test_returns_200_on_success(self, client):
        with patch("controllers.customers.model.delete_customer"):
            r = client.delete(f"/api/customers/{CUSTOMER_ID}")
        assert r.status_code == 200

    def test_response_status_is_success(self, client):
        with patch("controllers.customers.model.delete_customer"):
            r = client.delete(f"/api/customers/{CUSTOMER_ID}")
        assert body(r)["status"] == "success"

    def test_response_contains_customer_id(self, client):
        with patch("controllers.customers.model.delete_customer"):
            r = client.delete(f"/api/customers/{CUSTOMER_ID}")
        assert body(r)["id"] == CUSTOMER_ID

    def test_model_called_with_correct_id(self, client):
        with patch("controllers.customers.model.delete_customer") as m:
            client.delete(f"/api/customers/{CUSTOMER_ID}")
        m.assert_called_once_with(CUSTOMER_ID)

    # ── BUG-2: no error response when customer does not exist ─────────────────

    def test_bug2_delete_nonexistent_customer_still_returns_success(self, client):
        """
        BUG-2: delete_customer always returns status="success" regardless of
        whether the customer existed. There is no existence check and no
        error/warning path — the controller should return "error" or "warning"
        when the customer is not found.
        """
        # Simulate the model silently doing nothing (customer not found)
        with patch("controllers.customers.model.delete_customer"):
            r1 = client.delete(f"/api/customers/{CUSTOMER_ID}")
            r2 = client.delete(f"/api/customers/{CUSTOMER_ID}")  # second delete
        # BUG: both calls return "success" even though the second one
        # operates on a non-existent customer.
        assert body(r2)["status"] != "success", (
            "BUG-2: delete_customer returns 'success' even when the customer "
            "does not exist (no existence check in the controller)"
        )

    # ── wrong method ──────────────────────────────────────────────────────────

    def test_get_not_allowed_on_delete_path(self, client):
        """GET /api/customers/<id> IS allowed (it fetches the customer) — just a sanity check."""
        with patch("controllers.customers.model.get_customers", return_value=[CUSTOMER_ROW_DETAIL]):
            r = client.get(f"/api/customers/{CUSTOMER_ID}")
        assert r.status_code == 200

    def test_patch_not_allowed(self, client):
        r = client.patch(f"/api/customers/{CUSTOMER_ID}")
        assert r.status_code == 405


# ══════════════════════════════════════════════════════════════════════════════
# Pure helper functions  (no HTTP, no mocking needed)
# ══════════════════════════════════════════════════════════════════════════════

class TestDetectPhones:
    """Unit tests for controllers.customers.detect_phones"""

    def setup_method(self):
        from controllers.customers import detect_phones
        self.detect = detect_phones

    def test_none_returns_empty_list(self):
        assert self.detect(None) == []

    def test_empty_string_returns_empty_list(self):
        assert self.detect("") == []

    def test_no_phone_in_comment(self):
        assert self.detect("no phone here") == []

    def test_detects_plus_format(self):
        result = self.detect("+3221234567")
        assert "+3221234567" in result

    def test_detects_zero_eight_digit_format(self):
        """0 followed by 8 digits → Belgian landline."""
        result = self.detect("tel: 021234567")
        assert len(result) > 0
        assert any("021234567" in p for p in result)

    def test_detects_slash_space_format(self):
        result = self.detect("02/123 45 67")
        assert len(result) > 0
        assert any("021234567" in p for p in result)

    def test_detects_slash_comma_format(self):
        # Pattern r'0\d{2}/\d{2},\d{2},\d{2}' requires 0 + 2 digits before /
        result = self.detect("021/23,45,67")
        assert len(result) > 0

    def test_detects_short_prefix_slash_space_format(self):
        result = self.detect("04/567 89 01")
        assert len(result) > 0

    def test_multiple_phones_all_detected(self):
        result = self.detect("02/123 45 67 and 03/456 78 90")
        assert len(result) >= 2

    def test_output_contains_only_digits_and_plus(self):
        result = self.detect("02/123 45 67")
        for phone in result:
            assert all(c.isdigit() or c == '+' for c in phone)

    def test_bug3_mobile_also_matches_phone_pattern(self):
        """
        BUG-3: r'0\\d{8}' matches the first 9 characters of 0491234567.
        detect_phones should NOT match mobile numbers.
        """
        result = self.detect("0491234567")
        # BUG: result is non-empty because 049123456 (first 9 chars) is matched
        assert result == [], (
            "BUG-3: detect_phones matches the first 9 digits of a 10-digit "
            "mobile number due to missing word-boundary / length anchor"
        )


class TestDetectMobiles:
    """Unit tests for controllers.customers.detect_mobiles"""

    def setup_method(self):
        from controllers.customers import detect_mobiles
        self.detect = detect_mobiles

    def test_none_returns_empty_list(self):
        assert self.detect(None) == []

    def test_empty_string_returns_empty_list(self):
        assert self.detect("") == []

    def test_no_mobile_in_comment(self):
        assert self.detect("no phone here") == []

    def test_detects_plus_eleven_digit_format(self):
        result = self.detect("+32491234567")
        assert "+32491234567" in result

    def test_detects_zero_nine_digit_format(self):
        result = self.detect("0491234567")
        assert len(result) > 0
        assert any("0491234567" in m for m in result)

    def test_detects_slash_space_format(self):
        result = self.detect("0491/23 45 67")
        assert len(result) > 0

    def test_detects_slash_comma_format(self):
        result = self.detect("0491/23,45,67")
        assert len(result) > 0

    def test_output_contains_only_digits_and_plus(self):
        result = self.detect("0491/23 45 67")
        for mobile in result:
            assert all(c.isdigit() or c == '+' for c in mobile)

    def test_landline_not_matched_as_mobile(self):
        """A 9-digit landline (0 + 8 digits) must NOT match the mobile pattern."""
        result = self.detect("021234567")
        assert result == []


class TestDetectEmails:
    """Unit tests for controllers.customers.detect_emails"""

    def setup_method(self):
        from controllers.customers import detect_emails
        self.detect = detect_emails

    def test_none_returns_empty_list(self):
        assert self.detect(None) == []

    def test_empty_string_returns_empty_list(self):
        assert self.detect("") == []

    def test_no_email_in_comment(self):
        assert self.detect("no email here") == []

    def test_simple_email_detected(self):
        result = self.detect("contact: jean@acme.be")
        assert "jean@acme.be" in result

    def test_multiple_emails_all_detected(self):
        result = self.detect("a@b.com and c@d.org")
        assert "a@b.com" in result
        assert "c@d.org" in result

    def test_email_with_dots_in_local_part(self):
        result = self.detect("jean.dupont@acme.be")
        assert "jean.dupont@acme.be" in result

    def test_email_with_plus_in_local_part(self):
        result = self.detect("jean+tag@acme.be")
        assert "jean+tag@acme.be" in result

    def test_invalid_email_not_detected(self):
        assert self.detect("notanemail") == []

    def test_email_without_tld_not_detected(self):
        assert self.detect("user@nodot") == []


class TestIsOldDbComment:
    """Unit tests for controllers.customers.is_old_db_comment — BUG-4 exposed."""

    def setup_method(self):
        from controllers.customers import is_old_db_comment
        self.fn = is_old_db_comment

    def test_none_is_old(self):
        """None → old DB record (no comment at all)."""
        assert self.fn(None) is True

    def test_plain_text_is_old(self):
        """A plain text comment without ## markers is old-style."""
        assert self.fn("just a plain comment") is True

    def test_bug4_new_style_comment_wrongly_reported_as_old(self):
        """
        BUG-4: The function returns
          not (comment.startswith('##') and comment.endswith('##'))
        For a new-style comment '##data##' this evaluates to
          not (True and True) == not True == False
        But the function is named is_old_db_comment, so it should return
        False for a NEW-style comment (##...##) and True for an OLD-style
        comment. The logic is correct — what the test confirms is that
        '##data##' is NOT considered old, i.e. the return is False.
        """
        new_style = "##structured data##"
        result = self.fn(new_style)
        # A new-style comment is NOT old → expected False
        assert result is False, (
            "BUG-4: is_old_db_comment returns True for a new-style '##...##' "
            "comment, but it should return False (it is NOT old)."
        )

    def test_comment_starting_with_hash_but_not_ending(self):
        """Only starts with ## but doesn't end with ## → considered old."""
        assert self.fn("##only start") is True

    def test_comment_ending_with_hash_but_not_starting(self):
        """Only ends with ## but doesn't start with ## → considered old."""
        assert self.fn("only end##") is True

    def test_empty_string_is_old(self):
        """An empty string has no ## markers → old-style."""
        assert self.fn("") is True


class TestGetCustomerStreet:
    """Unit tests for models.customers.get_customer_street"""

    def setup_method(self):
        from models.customers import get_customer_street
        self.fn = get_customer_street

    def test_extracts_street_part(self):
        assert self.fn("Rue de la Paix , 1") == "Rue de la Paix"

    def test_strips_whitespace(self):
        assert self.fn("  Main Street  , 5") == "Main Street"

    def test_no_comma_returns_full_string(self):
        assert self.fn("NoComma") == "NoComma"

    def test_empty_string(self):
        assert self.fn("") == ""

    def test_multiple_commas_returns_only_first_part(self):
        assert self.fn("Street , 10, box 3") == "Street"


class TestGetCustomerStreetNumber:
    """Unit tests for models.customers.get_customer_street_number"""

    def setup_method(self):
        from models.customers import get_customer_street_number
        self.fn = get_customer_street_number

    def test_extracts_number_part(self):
        assert self.fn("Rue de la Paix , 1") == "1"

    def test_strips_whitespace(self):
        assert self.fn("Street ,  42  ") == "42"

    def test_no_comma_returns_empty_string(self):
        assert self.fn("NoComma") == ""

    def test_empty_string_returns_empty(self):
        assert self.fn("") == ""

    def test_multiple_commas_joins_remaining_parts(self):
        """Everything after the first comma is the number (e.g. 'bus 3')."""
        result = self.fn("Street , 10, box 3")
        assert "10" in result
        assert "box 3" in result

