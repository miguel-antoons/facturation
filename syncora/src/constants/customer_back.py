import re
from typing import Annotated, Any, NotRequired, ReadOnly, TypedDict

from pydantic import Field, computed_field, field_validator, model_validator

from constants.all import SyncoraModel, SyncoraUndefined, Undefined

PARTY_TYPE_CUSTOMER = "Customer"
ADDRESS_TYPE_INVOICE_ADDRESS = "InvoiceAddress"

# * ------------------------------------------
# * DATABASE FIELD NAMES FOR CUSTOMER INFORMATION
# * ------------------------------------------
CUSTOMER_DB_ID = "Numero"
CUSTOMER_DB_NAME = "Nom"
CUSTOMER_DB_FIRSTNAME = "Prenom"
CUSTOMER_DB_COMPANY = "Societe"
CUSTOMER_DB_COMMENT = "Commentaire"
CUSTOMER_DB_ADDRESS = "Adresse"
CUSTOMER_DB_POSTAL_CODE = "Codepostal"
CUSTOMER_DB_CITY = "Localite"
CUSTOMER_DB_VAT_NUMBER = "TVA"
CUSTOMER_DB_LANGUAGE = "Langue"
CUSTOMER_DB_ARCHITECT_NAME = "Nom Architecte"
CUSTOMER_DB_SALUTATION = "Titre"


class CustomerFront(TypedDict):
    id: Annotated[int, ReadOnly]
    name: str
    surname: str
    company: str
    comment: NotRequired[str]
    street: NotRequired[str]
    number: NotRequired[str]
    postal_code: str
    city: str
    vat_number: NotRequired[str]
    language: NotRequired[str]
    architect_name: NotRequired[str]
    salutation: NotRequired[str]
    phones: NotRequired[list[str]]
    hasEmail: NotRequired[bool]
    hasVAT: NotRequired[bool]


CustomerDB = TypedDict(
    "CustomerDB",
    {
        CUSTOMER_DB_ID: NotRequired[ReadOnly[int]],
        CUSTOMER_DB_NAME: NotRequired[str],
        CUSTOMER_DB_FIRSTNAME: NotRequired[str],
        CUSTOMER_DB_COMPANY: NotRequired[str],
        CUSTOMER_DB_COMMENT: NotRequired[str],
        CUSTOMER_DB_ADDRESS: NotRequired[str],
        CUSTOMER_DB_POSTAL_CODE: NotRequired[str],
        CUSTOMER_DB_CITY: NotRequired[str],
        CUSTOMER_DB_VAT_NUMBER: NotRequired[str],
        CUSTOMER_DB_LANGUAGE: NotRequired[str],
        CUSTOMER_DB_ARCHITECT_NAME: NotRequired[str],
        CUSTOMER_DB_SALUTATION: NotRequired[str],
    },
)


class CustomerBack(SyncoraModel):
    id: int = Field(default=-1, alias=CUSTOMER_DB_ID)
    name: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_NAME)
    surname: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_FIRSTNAME)
    company: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_COMPANY)
    comment: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_COMMENT)
    address: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_ADDRESS)
    postal_code: str | None = Field(
        default=SyncoraUndefined, alias=CUSTOMER_DB_POSTAL_CODE
    )
    city: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_CITY)
    vat_number: str | None = Field(
        default=SyncoraUndefined, alias=CUSTOMER_DB_VAT_NUMBER
    )
    language: str | None = Field(default=SyncoraUndefined, alias=CUSTOMER_DB_LANGUAGE)
    architect_name: str | None = Field(
        default=SyncoraUndefined, alias=CUSTOMER_DB_ARCHITECT_NAME
    )
    salutation: str | None = Field(
        default=SyncoraUndefined, alias=CUSTOMER_DB_SALUTATION
    )

    @staticmethod
    def from_db(field_names: list[str], data: list) -> CustomerBack:
        customer_db = CustomerDB(
            **{field: data[field_names.index(field)] for field in field_names}
        )
        return CustomerBack.model_validate(customer_db)

    def to_db(self) -> tuple[list[str], list[Any]]:
        mapping = self.model_dump(
            by_alias=True,
            exclude_unset=True,
            exclude_computed_fields=True,
            exclude={"id"},
        )

        fields = []
        values = []
        for field, value in mapping.items():
            fields.append(f"`{field}`")
            values.append(value if value else None)

        return fields, values

    def to_front(self) -> dict[str, Any]:
        return self.model_dump(
            exclude_defaults=True,
            exclude_unset=True,
            exclude={
                "id",
                "address",
                "emails",
                "telephoneNumbers",
                "mobileNumbers",
            },
        )

    @computed_field
    def street(self) -> str:
        if not self.address:
            return self.ret_def(self.address, "")
        parts = self.address.split(",")
        return parts[0].strip() if len(parts) > 0 else ""

    @computed_field
    def number(self) -> str:
        if not self.address:
            return self.ret_def(self.address, "")
        parts = self.address.split(",")
        return "".join(parts[1:]).strip() if len(parts) > 1 else ""

    @computed_field
    def emails(self) -> list[str]:
        if not self.comment:
            return []

        pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        return re.findall(pattern, self.comment)

    @computed_field
    def telephoneNumbers(self) -> list[str] | Undefined:  # noqa: N802
        if not self.comment:
            return []

        patterns = [
            r"(?<!\d)\+\d{10}(?!\d)",
            r"(?<!\d)0\d{8}(?!\d)",
            r"(?<!\d)0\d{2}/\d{2} \d{2} \d{2}(?!\d)",
            r"(?<!\d)0\d{2}/\d{2},\d{2},\d{2}(?!\d)",
            r"(?<!\d)0\d{1}/\d{3} \d{2} \d{2}(?!\d)",
            r"(?<!\d)0\d{1}/\d{3},\d{2},\d{2}(?!\d)",
        ]
        phone_numbers = []

        for pattern in patterns:
            phone_numbers.extend(re.findall(pattern, self.comment))

        cleaned_phone_numbers = []
        for number in phone_numbers:
            cleaned_phone_numbers.append(re.sub(r"[^\d+]", "", number))

        return cleaned_phone_numbers

    @computed_field
    def mobileNumbers(self) -> list[str]:  # noqa: N802
        if not self.comment:
            return []

        patterns = [
            r"(?<!\d)\+\d{11}(?!\d)",
            r"(?<!\d)0\d{9}(?!\d)",
            r"(?<!\d)0\d{3}/\d{2} \d{2} \d{2}(?!\d)",
            r"(?<!\d)0\d{3}/\d{2},\d{2},\d{2}(?!\d)",
        ]
        mobile_numbers = []

        for pattern in patterns:
            mobile_numbers.extend(re.findall(pattern, self.comment))

        cleaned_mobile_numbers = []
        for number in mobile_numbers:
            cleaned_mobile_numbers.append(re.sub(r"[^\d+]", "", number))

        return cleaned_mobile_numbers

    @computed_field
    def hasVAT(self) -> bool:  # noqa: N802
        return self.ret_def(self.vat_number, bool(self.vat_number))

    @computed_field
    def hasEmail(self) -> bool:  # noqa: N802
        return self.ret_def(self.emails, bool(self.emails))

    @model_validator(mode="before")
    @classmethod
    def assemble_address_from_front(cls, data: Any) -> Any:  # noqa: ANN401
        if (
            isinstance(data, dict)
            and "address" not in data
            and CUSTOMER_DB_ADDRESS not in data
            and ("street" in data or "number" in data)
        ):
            street = data.get("street", "")
            number = data.get("number", "")
            data["address"] = f"{street} , {number}"
        return data

    @field_validator("language", mode="after")
    @classmethod
    def ensure_language_lower(cls, language: str | Undefined) -> str | None | Undefined:
        if language:
            return language.lower()
        return language
