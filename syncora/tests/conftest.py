"""Shared fixtures for the Syncora test suite.

The backend talks to three external systems (MongoDB, MS Access, Billit HTTP).
None of them are available in the test environment, so they are replaced here:

* MongoDB  -> an in-memory ``mongomock`` database behind the real
  ``OrderModel`` code path (so persistence is exercised for real).
* MS Access -> a tiny in-memory store behind the real ``CustomerModel``
  interface (no JVM, no .accdb).
* Billit    -> the ``responses`` library, which records every outbound
  ``requests`` call so tests can assert on method/URL/headers/body.

The real ``.env`` is never read; ``dotenv_values`` is patched to return a
fixed dict (see ``FAKE_ENV``).
"""

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import mongomock
import pytest
import responses

from app import create_app
from models import order_model
from models.customers import CustomerModel

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask
    from flask.testing import FlaskClient

    from constants.customer_back import CustomerBack

# A fixed environment used in place of the real .env. The values are
# meaningless but stable; tests reference them (e.g. the Billit base URL).
FAKE_ENV: dict[str, str] = {
    "URL": "https://billit.test.local/v1",
    "API_SECRET": "test-api-secret",
    "PARTY_ID": "test-party-id",
    "MONGO_USER": "u",
    "MONGO_PWD": "p",
    "MONGO_IP": "localhost",
    "MONGO_PORT": "27017",
    "MONGO_DB": "syncora_test",
    "DB_FILE": "/tmp/nonexistent.accdb",
}


# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #
@pytest.fixture(autouse=True)
def fake_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Replace ``dotenv_values`` everywhere it is imported (never reads .env)."""

    def _values(_path: str | None = None) -> dict[str, str]:
        return FAKE_ENV

    for module in (
        "controllers.billit",
        "utils.peppol_poller",
        "database.mongodb",
        "database.access",
    ):
        monkeypatch.setattr(f"{module}.dotenv_values", _values)
    return FAKE_ENV


# --------------------------------------------------------------------------- #
# MongoDB (mongomock) behind the real OrderModel
# --------------------------------------------------------------------------- #
@pytest.fixture
def mongo(monkeypatch: pytest.MonkeyPatch) -> mongomock.Database:
    """A fresh in-memory Mongo database for each test.

    The real ``OrderModel.get_connection`` is patched, so ``BillModel`` /
    ``CnoteModel`` (which inherit it) run their real persistence code against
    mongomock.
    """
    client = mongomock.MongoClient()
    db = client[FAKE_ENV["MONGO_DB"]]

    @contextlib.contextmanager
    def fake_get_connection() -> Generator[Any]:
        yield db

    monkeypatch.setattr(order_model, "get_connection", fake_get_connection)
    return db


# --------------------------------------------------------------------------- #
# Customers (in-memory store behind the CustomerModel interface)
# --------------------------------------------------------------------------- #
class FakeCustomerStore:
    """In-memory replacement for the MS Access ``Client`` table.

    Stored objects are real ``CustomerBack`` instances, so every computed
    field (street/number, emails, hasVAT, ...) is exercised. The public methods
    mirror ``CustomerModel``'s signatures so the controllers cannot tell the
    difference.
    """

    def __init__(self) -> None:
        self.data: dict[int, CustomerBack] = {}
        self._next_id = 1

    def seed(self, customer: CustomerBack) -> CustomerBack:
        if getattr(customer, "id", None) in (None, -1):
            customer.id = self._next_id
        self.data[customer.id] = customer
        self._next_id = max(self._next_id, customer.id + 1)
        return customer

    def get(
        self,
        fields: list[str],  # noqa: ARG002 -- accepted for interface parity
        *,
        filters: dict[str, Any] | None = None,
        by_id: bool = False,
    ) -> list[CustomerBack] | dict[int, CustomerBack]:
        items = list(self.data.values())
        if filters:
            for key, value in filters.items():
                items = [
                    c for c in items if c.model_dump(by_alias=True).get(key) == value
                ]
        return {c.id: c for c in items} if by_id else items

    def create(self, data: CustomerBack) -> int:
        data.id = self._next_id
        self.data[data.id] = data
        self._next_id += 1
        return data.id

    def update(self, customer_id: int, data: CustomerBack) -> None:
        data.id = customer_id
        self.data[customer_id] = data

    def delete(self, customer_id: int) -> None:
        self.data.pop(customer_id, None)

    def contains(self, customer_id: int) -> bool:
        return customer_id in self.data


@pytest.fixture
def customer_store(monkeypatch: pytest.MonkeyPatch) -> FakeCustomerStore:
    """Replace ``CustomerModel``'s data methods with an in-memory store.

    ``get_one`` is left as the real implementation on purpose: it composes
    ``CustomerModel.get(...)[0]``, so a missing id raises ``IndexError`` --
    exactly the current (gap) behaviour the spec wants pinned.
    """
    store = FakeCustomerStore()

    def _get(
        fields: list[str],
        *,
        filters: dict[str, Any] | None = None,
        by_id: bool = False,
    ) -> list[CustomerBack] | dict[int, CustomerBack]:
        return store.get(fields, filters=filters, by_id=by_id)

    def _create(data: CustomerBack) -> int:
        return store.create(data)

    def _update(customer_id: int, data: CustomerBack) -> None:
        store.update(customer_id, data)

    def _delete(customer_id: int) -> None:
        store.delete(customer_id)

    def _contains(customer_id: int) -> bool:
        return store.contains(customer_id)

    monkeypatch.setattr(CustomerModel, "get", _get)
    monkeypatch.setattr(CustomerModel, "create", _create)
    monkeypatch.setattr(CustomerModel, "update", _update)
    monkeypatch.setattr(CustomerModel, "delete", _delete)
    monkeypatch.setattr(CustomerModel, "contains", _contains)
    return store


# --------------------------------------------------------------------------- #
# Flask app + test client
# --------------------------------------------------------------------------- #
@pytest.fixture
def app() -> Flask:
    return create_app()


@pytest.fixture
def client(
    app: Flask,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> FlaskClient:
    app.testing = True
    return app.test_client()


# --------------------------------------------------------------------------- #
# Billit HTTP mock (records outbound requests; never hits the network)
# --------------------------------------------------------------------------- #
@pytest.fixture
def billit_fake() -> Generator[responses.RequestsMock]:
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


# --------------------------------------------------------------------------- #
# PDF generation stub (used by Billit-flow tests that are not about PDF bytes)
# --------------------------------------------------------------------------- #
@pytest.fixture
def fake_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub out WeasyPrint PDF generation with deterministic dummy bytes."""
    monkeypatch.setattr(
        "controllers.bill_gen.create_bill", lambda *a, **k: b"%PDF-1.4 fake"
    )
    monkeypatch.setattr(
        "controllers.cnote_gen.create_cnote", lambda *a, **k: b"%PDF-1.4 fake"
    )


# --------------------------------------------------------------------------- #
# Peppol poller
# --------------------------------------------------------------------------- #
@pytest.fixture
def poller_spy(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Replace ``PeppolStatusPoller`` in the controllers with a recording stub.

    Returns the list of externalIds that were polled. Lets API-level tests
    assert "a poll was/was not started" without spawning daemon threads.
    """
    calls: list[int] = []

    class _Spy:
        def __init__(self, callback: object, **_kwargs: object) -> None:
            self.callback = callback

        def __call__(self, order_id: int) -> None:
            calls.append(order_id)

    monkeypatch.setattr("controllers.bills.PeppolStatusPoller", _Spy)
    monkeypatch.setattr("controllers.cnotes.PeppolStatusPoller", _Spy)
    return calls


@pytest.fixture
def poller(monkeypatch: pytest.MonkeyPatch) -> type:
    """Yield the real ``PeppolStatusPoller`` class with its singleton reset.

    Tests build a poller with short intervals and drive the coroutine
    directly (``asyncio.run``) against the ``billit_fake`` HTTP mock.
    """
    from utils.peppol_poller import PeppolStatusPoller

    PeppolStatusPoller._instance = None
    yield PeppolStatusPoller
    PeppolStatusPoller._instance = None


# --------------------------------------------------------------------------- #
# PDF / integration helpers
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def chdir_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run PDF generation with CWD at the repo root (relative template paths)."""
    monkeypatch.chdir(REPO_ROOT)


@pytest.fixture
def weasyprint() -> None:
    """Skip the test when WeasyPrint (and its system deps) is unavailable."""
    pytest.importorskip("weasyprint")
