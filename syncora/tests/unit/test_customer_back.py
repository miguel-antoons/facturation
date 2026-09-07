"""CustomerBack pure-logic unit tests (§2.3, §5.7, FR-CUS-6..9).

Address split, contact extraction from the comment, hasVAT/hasEmail, language
lowercasing, and the street+number -> Adresse assembly. These exercise the
model directly; the HTTP contract is covered in ``tests/api/test_customers.py``.
"""

import pytest

from constants.all import Undefined
from constants.customer_back import CustomerBack


def customer(**kwargs: object) -> CustomerBack:
    """Build a CustomerBack from Access-style aliases."""
    return CustomerBack.model_validate(kwargs)


# --- Address split (FR-CUS-2, TC-CUS-7..10) ------------------------------ #
def test_street_and_number_split_on_comma() -> None:
    c = customer(Adresse="Rue X, 12")
    assert c.street == "Rue X"
    assert c.number == "12"


def test_address_no_comma_keeps_whole_string_as_street() -> None:
    c = customer(Adresse="Avenue Louise")
    assert c.street == "Avenue Louise"
    assert c.number == ""


def test_address_multiple_commas_joins_remainder_as_number() -> None:
    c = customer(Adresse="Rue X, 12, Box 3")
    assert c.street == "Rue X"
    assert c.number == "12 Box 3"


def test_address_empty_gives_empty_strings_not_none() -> None:
    c = customer(Adresse="")
    assert c.street == ""
    assert c.number == ""


# --- Contact extraction (FR-CUS-8, TC-CUS-3/4) --------------------------- #
def test_no_comment_means_no_emails_or_phones() -> None:
    c = customer(Commentaire=None)
    assert c.emails == []
    assert c.mobileNumbers == []
    assert c.telephoneNumbers == []
    assert c.hasEmail is False


def test_comment_with_email_and_mobile_is_parsed() -> None:
    c = customer(Commentaire="contact: a@b.com ou 0475/12 34 56")
    assert c.emails == ["a@b.com"]
    assert c.mobileNumbers == ["0475123456"]
    assert c.hasEmail is True


# --- hasVAT / hasEmail (FR-CUS-9, TC-CUS-5) ------------------------------ #
def test_hasvat_reflects_vat_number_presence() -> None:
    assert customer(TVA="BE0123456789").hasVAT is True
    assert customer(TVA="").hasVAT is False


def test_hasemail_false_without_email_in_comment() -> None:
    c = customer(Commentaire="just text, no email", TVA="")
    assert c.hasEmail is False
    assert c.hasVAT is False


# --- Language lowercasing (FR-CUS-7, TC-CUS-15/16) ----------------------- #
@pytest.mark.parametrize("lang", ["FR", "fr", "NL", "nl"])
def test_language_is_stored_lowercased(lang: str) -> None:
    assert customer(Langue=lang).language == lang.lower()


# --- Address assembly on input (FR-CUS-6, TC-CUS-13/19/20) -------------- #
def test_street_and_number_are_assembled_into_address() -> None:
    c = CustomerBack.model_validate(
        {
            "name": "Doe",
            "street": "Rue Y",
            "number": "5",
            "postal_code": "1000",
            "city": "Bx",
            "language": "FR",
        },
        by_name=True,
    )
    assert c.address == "Rue Y , 5"
    assert c.street == "Rue Y"
    assert c.number == "5"


def test_explicit_address_overrides_assembly() -> None:
    c = CustomerBack.model_validate(
        {"name": "Doe", "address": "Explicit 1", "postal_code": "1000", "city": "Bx"},
        by_name=True,
    )
    assert c.address == "Explicit 1"


def test_street_only_assembles_trailing_empty_number() -> None:
    c = CustomerBack.model_validate(
        {"name": "Doe", "street": "Rue Z", "postal_code": "1000", "city": "Bx"},
        by_name=True,
    )
    assert c.address == "Rue Z , "


# --- to_db / to_front shape --------------------------------------------- #
def test_to_db_returns_aliased_fields_and_values() -> None:
    c = CustomerBack.model_validate(
        {
            "name": "Doe",
            "street": "Rue Y",
            "number": "5",
            "postal_code": "1000",
            "city": "Bx",
            "language": "FR",
        },
        by_name=True,
    )
    fields, values = c.to_db()
    assert "`Adresse`" in fields
    assert "Rue Y , 5" in values
    assert "fr" in values  # language lowercased


def test_undefined_is_falsy_and_singleton() -> None:
    assert not Undefined()
    assert Undefined() is Undefined()
