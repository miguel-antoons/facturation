import re
from typing import TypedDict, NotRequired, ReadOnly, Annotated, Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

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


CustomerDB = TypedDict("CustomerDB", {
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
})


class CustomerBack(BaseModel):
    id: int = Field(default=-1, validation_alias=CUSTOMER_DB_ID)
    name: str | None = Field(default=None, validation_alias=CUSTOMER_DB_NAME)
    surname: str | None = Field(default=None, validation_alias=CUSTOMER_DB_FIRSTNAME)
    company: str | None = Field(default=None, validation_alias=CUSTOMER_DB_COMPANY)
    comment: str | None = Field(default=None, validation_alias=CUSTOMER_DB_COMMENT)
    address: str | None = Field(default=None, validation_alias=CUSTOMER_DB_ADDRESS)
    postal_code: str | None = Field(default=None, validation_alias=CUSTOMER_DB_POSTAL_CODE)
    city: str | None = Field(default=None, validation_alias=CUSTOMER_DB_CITY)
    vat_number: str | None = Field(default=None, validation_alias=CUSTOMER_DB_VAT_NUMBER)
    language: str | None = Field(default=None, validation_alias=CUSTOMER_DB_LANGUAGE)
    architect_name: str | None = Field(default=None, validation_alias=CUSTOMER_DB_ARCHITECT_NAME)
    salutation: str | None = Field(default=None, validation_alias=CUSTOMER_DB_SALUTATION)


    @staticmethod
    def from_customer_db(field_names: list[str], data: list):
        customer_db = CustomerDB(
            **{field: data[field_names.index(field)] for field in field_names}
        )
        return CustomerBack.model_validate(customer_db)


    def to_customer_db(self) -> tuple[list[str], list]:
        mapping = {
            CUSTOMER_DB_NAME: self.name,
            CUSTOMER_DB_FIRSTNAME: self.surname,
            CUSTOMER_DB_COMPANY: self.company,
            CUSTOMER_DB_COMMENT: self.comment,
            CUSTOMER_DB_ADDRESS: self.address,
            CUSTOMER_DB_POSTAL_CODE: self.postal_code,
            CUSTOMER_DB_CITY: self.city,
            CUSTOMER_DB_VAT_NUMBER: self.vat_number,
            CUSTOMER_DB_LANGUAGE: self.language,
            CUSTOMER_DB_ARCHITECT_NAME: self.architect_name,
            CUSTOMER_DB_SALUTATION: self.salutation,
        }
        
        fields = []
        values = []
        for field, value in mapping.items():
            if value is not None:
                fields.append(field)
                values.append(value if value else None)

        return fields, values


    @computed_field
    def street(self) -> str:
        if not self.address:
            return ""
        parts = self.address.split(',')
        return parts[0].strip() if len(parts) > 0 else ''


    @computed_field
    def number(self) -> str:
        if not self.address:
            return ""
        parts = self.address.split(',')
        return ''.join(parts[1:]).strip() if len(parts) > 1 else ''


    @computed_field
    def emails(self) -> list[str]:
        if self.comment is None:
            return []

        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(pattern, self.comment)


    @computed_field
    def telephone_numbers(self) -> list[str]:
        if self.comment is None:
            return []

        patterns = [
            r'\+\d{10}',
            r'0\d{8}',
            r'0\d{2}/\d{2} \d{2} \d{2}',
            r'0\d{2}/\d{2},\d{2},\d{2}',
            r'0\d{1}/\d{3} \d{2} \d{2}',
            r'0\d{1}/\d{3},\d{2},\d{2}',
        ]
        phone_numbers = []

        for pattern in patterns:
            phone_numbers.extend(re.findall(pattern, self.comment))

        cleaned_phone_numbers = []
        for number in phone_numbers:
            cleaned_phone_numbers.append(re.sub(r'[^\d+]', '', number))

        return cleaned_phone_numbers


    @computed_field
    def mobile_numbers(self) -> list[str]:
        if self.comment is None:
            return []

        patterns = [
            r'\+\d{11}',
            r'0\d{9}',
            r'0\d{3}/\d{2} \d{2} \d{2}',
            r'0\d{3}/\d{2},\d{2},\d{2}',
        ]
        mobile_numbers = []

        for pattern in patterns:
            mobile_numbers.extend(re.findall(pattern, self.comment))

        cleaned_mobile_numbers = []
        for number in mobile_numbers:
            cleaned_mobile_numbers.append(re.sub(r'[^\d+]', '', number))

        return cleaned_mobile_numbers


    @computed_field(alias="hasVAT")
    def has_vat(self) -> bool:
        return bool(self.vat_number)


    @computed_field(alias="hasEmail")
    def has_email(self) -> bool:
        return bool(self.emails)


    @model_validator(mode="before")
    @classmethod
    def assemble_address_from_front(cls, data: Any) -> Any:
        if isinstance(data, dict) and "address" not in data and CUSTOMER_DB_ADDRESS not in data:
            if "street" in data or "number" in data:
                street = data.get("street", "")
                number = data.get("number", "")
                data["address"] = f"{street} , {number}"
        return data


    @field_validator("language", mode="after")
    @classmethod
    def ensure_language_lower(cls, language: str) -> str | None:
        if language:
            return language.lower()
        return None
