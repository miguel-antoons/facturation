"""TC-FILE-1..6 and TC-PDF-1..13 : file endpoints and PDF content.

Bill/cnote PDFs are rendered with WeasyPrint, which needs the repo root as CWD
(templates/CSS/conditions are loaded via relative paths -- see findings.md).
These tests are marked ``integration`` and skip when WeasyPrint is unavailable.
The customer info PDF uses ReportLab and is always available.
"""

import io
from typing import TYPE_CHECKING

import pytest

from tests.api.helpers import insert_bill, insert_cnote
from tests.helpers import make_customer_back, valid_object_id_str

if TYPE_CHECKING:
    import mongomock
    from flask.testing import FlaskClient

    from tests.conftest import FakeCustomerStore


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def pdf_text(pdf_bytes: bytes) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _seed_customer(
    customer_store: FakeCustomerStore, *, language: str = "fr", **kwargs: object
) -> None:
    customer_store.seed(make_customer_back(id=1, language=language, **kwargs))  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# File endpoints (TC-FILE-1..6)
# --------------------------------------------------------------------------- #
def test_get_customer_file_pdf(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-FILE-1 (ReportLab -- always available)
    _seed_customer(customer_store)
    resp = client.get("/api/files/customers/1")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.headers["Content-Disposition"] == "inline; filename=customer_1.pdf"
    assert len(resp.data) > 0


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_get_bill_file_pdf(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-FILE-2
    _seed_customer(customer_store)
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    resp = client.get(f"/api/files/bills/{bill_id}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert resp.headers["Content-Disposition"] == f"inline; filename=bill_{bill_id}.pdf"
    assert len(resp.data) > 0


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_get_cnote_file_pdf(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-FILE-3
    _seed_customer(customer_store)
    cnote_id = insert_cnote(mongo, customer_id=1)
    resp = client.get(f"/api/files/cnotes/{cnote_id}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    assert (
        resp.headers["Content-Disposition"] == f"inline; filename=cnote_{cnote_id}.pdf"
    )
    assert len(resp.data) > 0


@pytest.mark.gap
def test_get_customer_file_nonexistent_is_unhandled(client: FlaskClient) -> None:
    # TC-FILE-4
    with pytest.raises(IndexError):
        client.get("/api/files/customers/9999")


@pytest.mark.gap
def test_get_bill_file_nonexistent_is_unhandled(client: FlaskClient) -> None:
    # TC-FILE-5
    from utils.generic_error import SyncoraError

    with pytest.raises(SyncoraError):
        client.get(f"/api/files/bills/{valid_object_id_str()}")


def test_get_customer_file_non_integer_path_is_404(client: FlaskClient) -> None:
    # TC-FILE-6
    assert client.get("/api/files/customers/abc").status_code == 404


# --------------------------------------------------------------------------- #
# Bill / cnote PDF content (TC-PDF-1..8, 10..13)
# --------------------------------------------------------------------------- #
@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_fr_customer_has_fr_labels(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-1
    _seed_customer(customer_store, language="fr")
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "Facture" in text
    assert "TOTAL" in text


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_nl_customer_has_nl_labels(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-2
    _seed_customer(customer_store, language="nl")
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "Factuur" in text


@pytest.mark.integration
@pytest.mark.parametrize(
    ("code", "present"),
    [("2", True), ("4", False)],
    ids=["code-2-has-certificate", "code-4-no-certificate"],
)
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_six_percent_certificate_only_for_code_2(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
    code: str,
    present: bool,
) -> None:
    # TC-PDF-3 / TC-PDF-4
    _seed_customer(customer_store, language="fr")
    bill_id = insert_bill(
        mongo, customer_id=1, order_number="2026000001", ventilation_code=code
    )
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    # The FR 6% certificate starts with "Taux de TVA"
    assert ("Taux de TVA" in text) is present


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_reverse_charge_legal_text_for_code_21(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-5
    _seed_customer(customer_store, language="fr")
    bill_id = insert_bill(
        mongo, customer_id=1, order_number="2026000001", ventilation_code="21"
    )
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "Autoliquidation" in text


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_appends_general_conditions_multiple_pages(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-6
    _seed_customer(customer_store)
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    resp = client.get(f"/api/files/bills/{bill_id}")
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(resp.data))
    assert len(reader.pages) > 1


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_monetary_amounts_use_comma_separator(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-7
    _seed_customer(customer_store)
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "100,00" in text  # unit price 100.00 -> "100,00"


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_cnote_omits_delivery_date_and_ogm_shows_about_invoice(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-8
    _seed_customer(customer_store)
    cnote_id = insert_cnote(mongo, customer_id=1, about_invoice_number="2026-001")
    text = pdf_text(client.get(f"/api/files/cnotes/{cnote_id}").data)
    assert "2026-001" in text
    assert "+++" not in text  # no OGM structure


def test_pdf_customer_info_lists_documented_fields(
    client: FlaskClient, customer_store: FakeCustomerStore
) -> None:
    # TC-PDF-10 — ReportLab
    _seed_customer(
        customer_store,
        comment="a@b.com",
        architect_name="Architecte X",
    )
    text = pdf_text(client.get("/api/files/customers/1").data)
    for fragment in ("Num", "Soci", "TVA", "Langue", "Architecte", "Commentaire"):
        assert fragment in text


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_unit_column_hidden_when_all_units_empty(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-11
    _seed_customer(customer_store, language="fr")
    bill_id = insert_bill(
        mongo,
        customer_id=1,
        order_number="2026000001",
        order_lines=[
            {
                "description": "d",
                "quantity": 1,
                "unitPriceExcl": 100.0,
                "unit": "",
                "VATPercentage": 6.0,
            }
        ],
    )
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "UNITÉ" not in text  # unit column header is hidden


@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_salutation_shown_when_present(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-12
    _seed_customer(customer_store, language="fr", salutation="Mr.")
    bill_id = insert_bill(mongo, customer_id=1, order_number="2026000001")
    text = pdf_text(client.get(f"/api/files/bills/{bill_id}").data)
    assert "Mr." in text


@pytest.mark.gap
@pytest.mark.integration
@pytest.mark.usefixtures("chdir_repo", "weasyprint")
def test_pdf_empty_order_lines_raises_index_error(
    client: FlaskClient,
    mongo: mongomock.Database,
    customer_store: FakeCustomerStore,
) -> None:
    # TC-PDF-13 / TC-GAP-13 : format_dyn_data indexes orderLines[0]
    _seed_customer(customer_store)
    bill_id = insert_bill(mongo, customer_id=1, order_lines=[])
    with pytest.raises(IndexError):
        client.get(f"/api/files/bills/{bill_id}")
