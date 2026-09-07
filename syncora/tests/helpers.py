"""Factory helpers for building request payloads and model objects.

These keep tests short and readable: a minimal valid bill payload is
``make_bill_payload()``, a customer with an email+mobile is
``make_customer(comment=...)``, etc. Builders return plain dicts matching the
frontend contract (``03-api-specification.md``) unless noted.
"""

from typing import Any

from bson import ObjectId

from constants.customer_back import CustomerBack

# Default line: 1 unit at 100.00 excl, 6% VAT.
DEFAULT_LINE: dict[str, Any] = {
    "description": "Travaux",
    "quantity": 1,
    "unitPriceExcl": 100.0,
    "unit": "h",
    "VATPercentage": 6.0,
}


def make_order_line(
    *,
    description: str = "Travaux",
    quantity: float = 1,
    unit_price_excl: float = 100.0,
    unit: str = "h",
    vat: float = 6.0,
) -> dict[str, Any]:
    return {
        "description": description,
        "quantity": quantity,
        "unitPriceExcl": unit_price_excl,
        "unit": unit,
        "VATPercentage": vat,
    }


def make_bill_payload(
    *,
    customer_id: int = 1,
    order_number: str = "2026-001",
    order_title: str = "Chantier principal",
    ventilation_code: str = "2",
    order_date: str = "2026-09-06",
    expiry_date: str = "2026-09-20",
    delivery_date: str = "2026-09-06",
    lines: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Minimal valid POST /api/bills body (matches OrderFront)."""
    return {
        "customerId": customer_id,
        "orderNumber": order_number,
        "orderDate": order_date,
        "expiryDate": expiry_date,
        "deliveryDate": delivery_date,
        "orderTitle": order_title,
        "ventilationCode": ventilation_code,
        "orderLines": lines if lines is not None else [dict(DEFAULT_LINE)],
    }


def make_cnote_payload(
    *,
    customer_id: int = 1,
    order_number: str = "C2026-001",
    about_invoice_number: str = "2026-001",
    order_title: str = "Note de crédit",
    ventilation_code: str = "2",
    order_date: str = "2026-09-06",
    expiry_date: str = "2026-09-20",
    lines: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Minimal valid POST /api/cnotes body. ``deliveryDate`` is omitted, as the
    frontend does for credit notes."""
    return {
        "customerId": customer_id,
        "orderNumber": order_number,
        "aboutInvoiceNumber": about_invoice_number,
        "orderDate": order_date,
        "expiryDate": expiry_date,
        "orderTitle": order_title,
        "ventilationCode": ventilation_code,
        "orderLines": lines if lines is not None else [dict(DEFAULT_LINE)],
    }


def make_customer(
    *,
    name: str | None = "Dupont",
    surname: str | None = "Luc",
    company: str | None = "Acme",
    street: str = "Rue X",
    number: str = "12",
    postal_code: str = "1000",
    city: str = "Bruxelles",
    vat_number: str | None = "BE0123456789",
    language: str = "FR",
    comment: str | None = None,
    salutation: str | None = None,
    architect_name: str | None = None,
) -> dict[str, Any]:
    """Minimal valid POST /api/customers body (field names, as the frontend sends)."""
    body: dict[str, Any] = {
        "name": name,
        "surname": surname,
        "company": company,
        "street": street,
        "number": number,
        "postal_code": postal_code,
        "city": city,
        "language": language,
    }
    if vat_number is not None:
        body["vat_number"] = vat_number
    if comment is not None:
        body["comment"] = comment
    if salutation is not None:
        body["salutation"] = salutation
    if architect_name is not None:
        body["architect_name"] = architect_name
    return body


def make_customer_back(
    *,
    id: int = 1,  # noqa: A002 -- mirrors the Access column name
    name: str | None = "Dupont",
    surname: str | None = "Luc",
    company: str | None = "Acme",
    address: str = "Rue X, 12",
    postal_code: str = "1000",
    city: str = "Bruxelles",
    vat_number: str | None = "BE0123456789",
    language: str = "fr",
    comment: str | None = None,
    salutation: str | None = None,
    architect_name: str | None = None,
) -> CustomerBack:
    """Build a ``CustomerBack`` from Access-style aliases (as if read from DB)."""
    data: dict[str, Any] = {
        "Numero": id,
        "Nom": name,
        "Prenom": surname,
        "Societe": company,
        "Adresse": address,
        "Codepostal": postal_code,
        "Localite": city,
        "TVA": vat_number,
        "Langue": language,
    }
    if comment is not None:
        data["Commentaire"] = comment
    if salutation is not None:
        data["Titre"] = salutation
    if architect_name is not None:
        data["Nom Architecte"] = architect_name
    return CustomerBack.model_validate(data)


def valid_object_id_str() -> str:
    """A stable, valid 24-hex ObjectId string (not tied to a real insert)."""
    return str(ObjectId("507f1f77bcf86cd799439011"))
