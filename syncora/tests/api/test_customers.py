"""TC-CUS-1..27 : customer REST contract (FR-CUS-1..10, API-CUS-1..5)."""

from typing import TYPE_CHECKING

import pytest

from tests.helpers import make_customer, make_customer_back
from utils.generic_error import SyncoraError

if TYPE_CHECKING:
    import mongomock
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore

LIST_FIELDS = {
    "id",
    "name",
    "surname",
    "company",
    "postal_code",
    "city",
    "mobileNumbers",
    "telephoneNumbers",
    "hasVAT",
    "hasEmail",
}


# --- List customers (TC-CUS-1..5) ---------------------------------------- #
def test_list_customers_returns_exact_field_set(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-1
    customer_store.seed(make_customer_back(id=1, company="Acme"))
    customer_store.seed(make_customer_back(id=2, name="Doe", surname="Jane"))

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    items = resp.get_json()
    assert len(items) == 2
    for item in items:
        assert set(item.keys()) == LIST_FIELDS


def test_list_customers_empty(client: FlaskClient) -> None:
    # TC-CUS-2
    resp = client.get("/api/customers")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_customer_no_comment_has_no_contacts(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-CUS-3
    customer_store.seed(make_customer_back(id=3, comment=None, vat_number=""))
    item = client.get("/api/customers").get_json()[0]
    assert item["hasEmail"] is False
    assert item["mobileNumbers"] == []
    assert item["telephoneNumbers"] == []


def test_list_customer_comment_with_email_and_mobile(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-4
    customer_store.seed(
        make_customer_back(id=4, comment="a@b.com 0475123456", vat_number="BE0")
    )
    item = client.get("/api/customers").get_json()[0]
    assert item["hasEmail"] is True
    assert item["mobileNumbers"] == ["0475123456"]
    assert item["hasVAT"] is True


def test_list_customer_with_vat_but_no_email(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-CUS-5
    customer_store.seed(
        make_customer_back(id=5, comment=None, vat_number="BE0123456789")
    )
    item = client.get("/api/customers").get_json()[0]
    assert item["hasVAT"] is True
    assert item["hasEmail"] is False


# --- Get one customer (TC-CUS-6..12) ------------------------------------- #
def test_get_customer_returns_stored_plus_computed_street_number(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-6
    customer_store.seed(make_customer_back(id=10, address="Rue X, 12"))
    body = _get_customer(client, 10)
    assert body["street"] == "Rue X"
    assert body["number"] == "12"
    # excluded fields
    for excluded in ("id", "address", "emails", "telephoneNumbers", "mobileNumbers"):
        assert excluded not in body


@pytest.mark.parametrize(
    ("address", "street", "number"),
    [
        ("Rue X, 12", "Rue X", "12"),  # TC-CUS-7
        ("Avenue Louise", "Avenue Louise", ""),  # TC-CUS-8
        ("Rue X, 12, Box 3", "Rue X", "12 Box 3"),  # TC-CUS-9
        ("", "", ""),  # TC-CUS-10
    ],
)
def test_get_customer_address_split(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
    address: str,
    street: str,
    number: str,
) -> None:
    customer_store.seed(make_customer_back(id=11, address=address))
    body = _get_customer(client, 11)
    assert body["street"] == street
    assert body["number"] == number


@pytest.mark.gap
def test_get_customer_nonexistent_id_is_unhandled(client: FlaskClient) -> None:
    # TC-CUS-11 / TC-GAP-2 family : no not-found guard -> IndexError propagates
    # (in production this is a 500; under TESTING it surfaces directly).
    with pytest.raises(IndexError):
        client.get("/api/customers/9999")


def test_get_customer_non_integer_path_is_404(client: FlaskClient) -> None:
    # TC-CUS-12 : Flask int converter rejects before the controller
    resp = client.get("/api/customers/not-an-int")
    assert resp.status_code == 404


# --- Create customer (TC-CUS-13..21) ------------------------------------- #
def test_create_customer_persists_assembled_address(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-13
    resp = client.post("/api/customers", json=make_customer())
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    new_id = body["id"]
    assert customer_store.data[new_id].address == "Rue X , 12"


@pytest.mark.usefixtures("customer_store")
def test_create_customer_company_only(client: FlaskClient) -> None:
    # TC-CUS-14
    resp = client.post(
        "/api/customers",
        json={"company": "Acme", "postal_code": "1000", "city": "Bx", "language": "FR"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


@pytest.mark.parametrize("lang", ["FR", "nl"])
def test_create_customer_lowercases_language(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
    lang: str,
) -> None:
    # TC-CUS-15 / TC-CUS-16
    resp = client.post("/api/customers", json=make_customer(language=lang))
    new_id = resp.get_json()["id"]
    assert customer_store.data[new_id].language == lang.lower()


def test_create_customer_explicit_address_overrides_assembly(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-19
    resp = client.post(
        "/api/customers",
        json={
            "name": "Doe",
            "address": "Explicit 1",
            "postal_code": "1000",
            "city": "Bx",
            "language": "FR",
        },
    )
    new_id = resp.get_json()["id"]
    assert customer_store.data[new_id].address == "Explicit 1"


def test_create_customer_street_only_assembles_trailing_empty_number(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-20
    resp = client.post(
        "/api/customers",
        json={
            "name": "Doe",
            "street": "Rue Z",
            "postal_code": "1000",
            "city": "Bx",
            "language": "FR",
        },
    )
    new_id = resp.get_json()["id"]
    assert customer_store.data[new_id].address == "Rue Z , "


def test_create_customer_returns_new_autonumber(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-21 : id reflects the inserted row's id
    resp = client.post("/api/customers", json=make_customer())
    new_id = resp.get_json()["id"]
    assert new_id in customer_store.data
    assert isinstance(new_id, int)


@pytest.mark.gap
def test_create_customer_without_name_surname_company_is_unhandled(
    client: FlaskClient,
) -> None:
    # TC-CUS-17 / TC-GAP-8 : SyncoraError 1000 is unhandled at the route layer
    with pytest.raises(SyncoraError):
        client.post(
            "/api/customers",
            json={
                "name": None,
                "surname": None,
                "company": None,
                "postal_code": "1000",
                "city": "Bx",
            },
        )


def test_create_customer_malformed_body_is_not_500(client: FlaskClient) -> None:
    # TC-CUS-18 : non-JSON body is rejected by Flask, not a 500 traceback
    resp = client.post("/api/customers", data="not-json", content_type="text/plain")
    assert resp.status_code in (400, 415)


# --- Update customer (TC-CUS-22..25) ------------------------------------- #
def test_update_customer_existing(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-CUS-22
    customer_store.seed(make_customer_back(id=20))
    resp = client.put("/api/customers/20", json=make_customer(name="New"))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"status": "success", "id": 20}
    assert customer_store.data[20].name == "New"


def test_update_customer_body_without_id_uses_path_id(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-23
    customer_store.seed(make_customer_back(id=21))
    resp = client.put(
        "/api/customers/21",
        json={"name": "X", "postal_code": "1000", "city": "Bx", "language": "FR"},
    )
    assert resp.get_json()["id"] == 21
    assert 21 in customer_store.data


def test_update_customer_body_id_cannot_override_path_id(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-CUS-24
    customer_store.seed(make_customer_back(id=22))
    resp = client.put(
        "/api/customers/22",
        json={
            "id": 999,
            "name": "X",
            "postal_code": "1000",
            "city": "Bx",
            "language": "FR",
        },
    )
    assert resp.get_json()["id"] == 22
    assert 22 in customer_store.data
    assert 999 not in customer_store.data


def test_update_customer_nonexistent_does_not_crash(client: FlaskClient) -> None:
    # TC-CUS-25 : no not-found check -> the row is created; returns success
    resp = client.put(
        "/api/customers/7777",
        json={"name": "Ghost", "postal_code": "1000", "city": "Bx", "language": "FR"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


# --- Delete customer (TC-CUS-26..27) ------------------------------------- #
def test_delete_customer_existing(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-CUS-26
    customer_store.seed(make_customer_back(id=30))
    resp = client.delete("/api/customers/30")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "success", "id": 30}
    assert 30 not in customer_store.data


def test_delete_customer_referenced_by_bill_succeeds(
    client: FlaskClient,
    customer_store: FakeCustomerStore,
    mongo: mongomock.Database,
) -> None:
    # TC-CUS-27 : no referential guard today (gap)
    from tests.api.helpers import insert_bill

    customer_store.seed(make_customer_back(id=31))
    insert_bill(mongo, customer_id=31)
    resp = client.delete("/api/customers/31")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"


# --- helper ------------------------------------------------------------- #
def _get_customer(client: FlaskClient, customer_id: int) -> dict[str, object]:
    """GET /api/customers/{id} returns a JSON string (not jsonify); parse it."""
    resp = client.get(f"/api/customers/{customer_id}")
    assert resp.status_code == 200
    import json

    return json.loads(resp.data)
