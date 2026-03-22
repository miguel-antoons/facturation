from typing import TypedDict, NotRequired, ReadOnly, Annotated

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


class CustomerBack(TypedDict):
    Numero: NotRequired[ReadOnly[int]]
    Nom: NotRequired[str]
    Prenom: NotRequired[str]
    Societe: NotRequired[str]
    Commentaire: NotRequired[str]
    Adresse: NotRequired[str]
    Codepostal: NotRequired[str]
    Localite: NotRequired[str]
    TVA: NotRequired[str]
    Langue: NotRequired[str]
    NomArchitecte: NotRequired[str]
    Titre: NotRequired[str]

key_to_db_mapping = {
    "Numero": CUSTOMER_DB_ID,
    "Nom": CUSTOMER_DB_NAME,
    "Prenom": CUSTOMER_DB_FIRSTNAME,
    "Societe": CUSTOMER_DB_COMPANY,
    "Commentaire": CUSTOMER_DB_COMMENT,
    "Adresse": CUSTOMER_DB_ADDRESS,
    "Codepostal": CUSTOMER_DB_POSTAL_CODE,
    "Localite": CUSTOMER_DB_CITY,
    "TVA": CUSTOMER_DB_VAT_NUMBER,
    "Langue": CUSTOMER_DB_LANGUAGE,
    "NomArchitecte": CUSTOMER_DB_ARCHITECT_NAME,
    "Titre": CUSTOMER_DB_SALUTATION,
}