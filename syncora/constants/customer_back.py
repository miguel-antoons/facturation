import re
from dataclasses import dataclass
from typing import TypedDict, NotRequired, ReadOnly, Annotated

from pydantic import BaseModel, model_validator, Field, computed_field

from constants.all import ResponseMessage, RESPONSE_ERROR, COUNTRY_CODE_BE


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


# * ------------------------------------------
# * API FIELD NAMES FOR CUSTOMER INFORMATION
# * ------------------------------------------
CUSTOMER_API_ID = "id"
CUSTOMER_API_NAME = "name"
CUSTOMER_API_FIRSTNAME = "surname"
CUSTOMER_API_COMPANY = "company"
CUSTOMER_API_COMMENT = "comment"
CUSTOMER_API_STREET = "street"
CUSTOMER_API_NUMBER = "number"
CUSTOMER_API_POSTAL_CODE = "postal_code"
CUSTOMER_API_CITY = "city"
CUSTOMER_API_VAT_NUMBER = "vat_number"
CUSTOMER_API_LANGUAGE = "language"
CUSTOMER_API_ARCHITECT_NAME = "architect_name"
CUSTOMER_API_SALUTATION = "salutation"
CUSTOMER_API_PHONES = "phones"
CUSTOMER_API_HAS_EMAIL = "hasEmail"
CUSTOMER_API_HAS_VAT = "hasVAT"
CUSTOMER_API_STATUS = "status"


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


class CustomerBillitAddress(TypedDict):
    AddressType: str
    Street: str
    StreetNumber: str
    Zipcode: str
    City: str
    CountryCode: str


CustomerDB = TypedDict("CustomerDB", {
    "Numero": NotRequired[ReadOnly[int]],
    "Nom": NotRequired[str],
    "Prenom": NotRequired[str],
    "Societe": NotRequired[str],
    "Commentaire": NotRequired[str],
    "Adresse": NotRequired[str],
    "Codepostal": NotRequired[str],
    "Localite": NotRequired[str],
    "TVA": NotRequired[str],
    "Langue": NotRequired[str],
    "Nom Architecte": NotRequired[str],
    "Titre": NotRequired[str],
})


class CustomerBack(BaseModel):
    id: int = Field(validation_alias=CUSTOMER_DB_ID)
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
        print(customer_db)
        return CustomerBack.model_validate(customer_db)


    def to_customer_db(self) -> tuple[list[str], list]:
        mapping = {
            CUSTOMER_DB_ID: self.id,
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
                values.append(value)
                
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


    @model_validator(mode="after")
    def ensure_identity(self) -> "CustomerBack":
        if self.name is None and self.surname is None and self.company is None:
            raise ValueError("At least one of name, surname, or company must be provided.")
        return self
