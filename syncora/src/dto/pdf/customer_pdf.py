from typing import TypedDict


class CustomerPDF(TypedDict):
    OfficialCompanyName: str
    ContactFullName: str
    Salutation: str
    StreetAndNumber: str
    ZipCode: str
    City: str
    CountryName: str
    VAT: str
    Nr: int
