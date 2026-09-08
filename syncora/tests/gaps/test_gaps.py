"""Remaining TC-GAP-* regression tests (§21). See conftest for inline cases."""

from typing import TYPE_CHECKING

import pytest

from tests.api.helpers import insert_bill, insert_cnote
from tests.helpers import make_customer_back

if TYPE_CHECKING:
    from pathlib import Path

    import mongomock
    import responses
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore


@pytest.mark.gap
def test_negative_total_unreachable_via_api_gated_instead(
    client: FlaskClient,
    mongo: mongomock.Database,
    billit_fake: responses.RequestsMock,
    fake_pdf: None,
    customer_store: FakeCustomerStore,
) -> None:
    """TC-GAP-6 / TC-NFR-1 : the spec expects a negative total to surface as a
    500 via the API. In practice the pre_billit line gate rejects a negative
    unit price with a *warning* before any total is computed, so the
    SyncoraError 903-905 path is unreachable through the API (it is only
    reachable at the model level -- see tests/unit/test_totals.py). Pinned
    here; see tests/findings.md.
    """
    customer_store.seed(make_customer_back(id=1))
    bill_id = insert_bill(
        mongo,
        order_number="2026000001",
        customer_id=1,
        order_lines=[
            {
                "description": "d",
                "quantity": 1,
                "unitPriceExcl": -50.0,
                "unit": "h",
                "VATPercentage": 6.0,
            }
        ],
    )
    resp = client.post(f"/api/bills/sendBillit/{bill_id}")
    assert resp.get_json()["status"] == "warning"
    assert len(billit_fake.calls) == 0


@pytest.mark.gap
def test_order_number_uniqueness_is_code_only_no_db_index(
    mongo: mongomock.Database,
) -> None:
    """TC-GAP-9 / TC-NFR-10 : nothing prevents two bills with the same
    orderNumber coexisting in Mongo (uniqueness is checked in controller code
    only, not via a unique index)."""
    mongo["bills"].insert_one({"orderNumber": "2026-001", "externalId": 0})
    mongo["bills"].insert_one({"orderNumber": "2026-001", "externalId": 0})
    assert mongo["bills"].count_documents({"orderNumber": "2026-001"}) == 2


@pytest.mark.gap
def test_billit_requests_have_no_timeout(
    monkeypatch: pytest.MonkeyPatch, fake_env: dict[str, str]
) -> None:
    """TC-GAP-10 / TC-NFR-15 : outbound Billit calls pass no timeout."""
    import controllers.billit as billit_mod

    recorded: dict[str, object] = {}

    class _FakeResp:
        status_code = 201
        content = b"true"
        text = "true"

        def json(self) -> int:
            return 201

    def fake_post(
        url: str, headers: object = None, json: object = None, **kwargs: object
    ) -> object:
        recorded["timeout"] = kwargs.get("timeout", "NOT_PASSED")
        return _FakeResp()

    monkeypatch.setattr(billit_mod.requests, "post", fake_post)
    billit_mod.send_peppol(42)
    assert recorded["timeout"] == "NOT_PASSED"


@pytest.mark.gap
@pytest.mark.integration
def test_pdf_generation_fails_outside_repo_root(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
    weasyprint: None,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """TC-GAP-12 : PDF generation reads templates/CSS via CWD-relative paths and
    fails when CWD is not the repo root."""
    monkeypatch.chdir(tmp_path)
    customer_store.seed(make_customer_back(id=1))
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    from jinja2 import TemplateNotFound

    with pytest.raises((TemplateNotFound, FileNotFoundError)):
        client.get(f"/api/files/bills/{bill_id}")


@pytest.mark.gap
def test_delete_cnote_warning_mentions_billit_not_peppol(
    client: FlaskClient, mongo: mongomock.Database
) -> None:
    """TC-GAP-15 : the undeletable-cnote warning says 'Billit' even though the
    guard is about Peppol status (wording inconsistency)."""
    cnote_id = insert_cnote(mongo, external_id=42, peppol_status=1)
    resp = client.delete(f"/api/cnotes/{cnote_id}")
    message = resp.get_json()["message"]
    assert "Billit" in message
    assert "Peppol" not in message


@pytest.mark.gap
def test_env_is_reread_on_every_billit_call(
    monkeypatch: pytest.MonkeyPatch, fake_env: dict[str, str]
) -> None:
    """TC-GAP-17 / NFR-PERF-3 : dotenv_values is invoked per call (3x in
    get_headers alone), not cached."""
    import controllers.billit as billit_mod

    count = {"n": 0}

    def counter(_path: str | None = None) -> dict[str, str]:
        count["n"] += 1
        return fake_env

    monkeypatch.setattr(billit_mod, "dotenv_values", counter)
    billit_mod.get_headers()
    assert count["n"] == 3
