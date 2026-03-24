import re
from dataclasses import dataclass
from typing import TypedDict, NotRequired, ReadOnly, Annotated

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


class CustomerBillit(TypedDict):
    Nr: int
    Name: str
    VATNumber: str
    Zipcode: str
    City: str
    Street: str
    StreetNumber: str
    CountryCode: str
    ContactFirstName: str
    ContactLastName: str
    Language: str
    Email: str
    Phone: str
    Mobile: str
    PartyType: str
    Addresses: list[CustomerBillitAddress]


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


@dataclass
class CustomerBack:
    id: int | None = None
    last_name: str | None = None
    first_name: str | None = None
    company: str | None = None
    comment: str | None = None
    address: str | None = None
    postal_code: str | None = None
    city: str | None = None
    vat_number: str | None = None
    language: str | None = None
    architect_name: str | None = None
    name_prefix: str | None = None

    @staticmethod
    def from_customer_front(customer_front: CustomerFront):
        return CustomerBack(
            id = customer_front.get(CUSTOMER_API_ID),
            last_name = customer_front.get(CUSTOMER_API_NAME),
            first_name = customer_front.get(CUSTOMER_API_FIRSTNAME),
            company = customer_front.get(CUSTOMER_API_COMPANY),
            comment = customer_front.get(CUSTOMER_API_COMMENT),
            address = customer_front.get(CUSTOMER_API_STREET),
            postal_code = customer_front.get(CUSTOMER_API_POSTAL_CODE),
            city = customer_front.get(CUSTOMER_API_CITY),
            vat_number = customer_front.get(CUSTOMER_API_VAT_NUMBER),
            language = customer_front.get(CUSTOMER_API_LANGUAGE),
            architect_name = customer_front.get(CUSTOMER_API_ARCHITECT_NAME),
            name_prefix = customer_front.get(CUSTOMER_API_SALUTATION),
        )

    @staticmethod
    def from_customer_db(customer_db: CustomerDB):
        return CustomerBack(
            id = customer_db.get(CUSTOMER_DB_ID),
            last_name = customer_db.get(CUSTOMER_DB_NAME),
            first_name = customer_db.get(CUSTOMER_DB_FIRSTNAME),
            company = customer_db.get(CUSTOMER_DB_COMPANY),
            comment = customer_db.get(CUSTOMER_DB_COMMENT),
            address = customer_db.get(CUSTOMER_DB_ADDRESS),
            postal_code = customer_db.get(CUSTOMER_DB_POSTAL_CODE),
            city = customer_db.get(CUSTOMER_DB_CITY),
            vat_number = customer_db.get(CUSTOMER_DB_VAT_NUMBER),
            language = customer_db.get(CUSTOMER_DB_LANGUAGE),
            architect_name = customer_db.get(CUSTOMER_DB_ARCHITECT_NAME),
            name_prefix = customer_db.get(CUSTOMER_DB_SALUTATION),
        )

    def to_customer_billit(self) -> CustomerBillit | ResponseMessage:
        if len(self.address.split(',')) <= 1:
            print("Invalid address format for customer ID:", self.id)
            return ResponseMessage(
                status=RESPONSE_ERROR,
                message="Format d'adresse incorrect. L'adresse devrait avoir le format 'Rue , Numéro'."
            )

        customer_emails = self.emails
        phones = self.telephone_numbers
        mobiles = self.mobile_numbers

        return CustomerBillit(
            Nr=self.id,
            Name=self.company,
            VATNumber=self.vat_number,
            Zipcode=self.postal_code,
            City=self.city,
            Street=self.street,
            StreetNumber=self.street_number,
            CountryCode=COUNTRY_CODE_BE,
            ContactFirstName=self.first_name,
            ContactLastName=self.last_name,
            Language=self.language.upper(),
            Email=customer_emails[0] if len(customer_emails) > 0 else "",
            Phone=phones[0] if len(phones) > 0 else "",
            Mobile=mobiles[0] if len(mobiles) > 0 else "",
            PartyType=PARTY_TYPE_CUSTOMER,
            Addresses=[
                CustomerBillitAddress(
                    AddressType=ADDRESS_TYPE_INVOICE_ADDRESS,
                    Street=self.street,
                    StreetNumber=self.street_number,
                    City=self.city,
                    Zipcode=self.postal_code,
                    CountryCode=COUNTRY_CODE_BE
                )
            ],
        )

    def to_customer_db(self) -> CustomerDB:
        db_cust = CustomerDB(
            Numero=self.id,
            Nom=self.last_name,
            Prenom=self.first_name,
            Societe=self.company,
            Commentaire=self.comment,
            Adresse=f"{self.street} , {self.street_number}" if self.street and self.street_number else None,
            Codepostal=self.postal_code,
            Localite=self.city,
            TVA=self.vat_number,
            Langue=self.language,
            Titre=self.name_prefix,
        )
        db_cust["Nom Architecte"] = self.architect_name
        for key in db_cust:
            if db_cust[key] is None:
                del db_cust[key]
        return db_cust

    @property
    def street(self) -> str:
        if not self.address:
            raise ValueError("Address is not set")
        parts = self.address.split(',')
        return parts[0].strip() if len(parts) > 0 else ''

    @property
    def street_number(self) -> str:
        if not self.address:
            raise ValueError("Address is not set")
        parts = self.address.split(',')
        return ''.join(parts[1:]).strip() if len(parts) > 1 else ''

    @property
    def emails(self) -> list[str]:
        if self.comment is None:
            return []

        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(pattern, self.comment)

    @property
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


    @property
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
