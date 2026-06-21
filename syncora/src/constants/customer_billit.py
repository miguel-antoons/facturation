from typing import Any

from pydantic import BaseModel, Field, field_validator, computed_field, model_validator

from constants.all import COUNTRY_CODE_BE
from constants.customer_back import PARTY_TYPE_CUSTOMER, ADDRESS_TYPE_INVOICE_ADDRESS
from utils.generic_error import SyncoraError, Severity


class CustomerBillit(BaseModel):
    Nr: int = Field(validation_alias="id", frozen=True)
    Name: str | None = Field(default=None, validation_alias="company", frozen=True)
    VATNumber: str | None = Field(default=None, validation_alias="vat_number", frozen=True)
    Zipcode: str = Field(validation_alias="postal_code", frozen=True, min_length=1)
    City: str = Field(validation_alias="city", frozen=True, min_length=1)
    Street: str = Field(validation_alias="street", frozen=True, min_length=1)
    StreetNumber: str = Field(validation_alias="number", frozen=True, min_length=1)
    CountryCode: str = Field(default=COUNTRY_CODE_BE, frozen=True)
    ContactFirstName: str | None = Field(default=None, validation_alias="surname", frozen=True)
    ContactLastName: str | None = Field(default=None, validation_alias="name", frozen=True)
    Language: str = Field(validation_alias="language", frozen=True, min_length=1)
    Email: str = Field(validation_alias="emails", frozen=True)
    Phone: str = Field(validation_alias="telephoneNumbers", frozen=True)
    Mobile: str = Field(validation_alias="mobileNumbers", frozen=True)
    PartyType: str = Field(default=PARTY_TYPE_CUSTOMER, frozen=True, min_length=1)

    @computed_field
    def Addresses(self) -> list[dict[str, str]]:
        return [
            {
                "AddressType": ADDRESS_TYPE_INVOICE_ADDRESS,
                "Street": self.Street,
                "StreetNumber": self.StreetNumber,
                "City": self.City,
                "Zipcode": self.Zipcode,
                "CountryCode": self.CountryCode,
            }
        ]

    @field_validator("Language", mode="after")
    @classmethod
    def upper_language(cls, language: str) -> str:
        return language.upper()

    @field_validator("Email", mode="before")
    @classmethod
    def extract_single_email(cls, emails: Any) -> Any:
        if isinstance(emails, list):
            return emails[0] if emails else ""
        return emails

    @field_validator("Phone", mode="before")
    @classmethod
    def extract_single_phone(cls, phones: Any) -> Any:
        if isinstance(phones, list):
            return phones[0] if phones else ""
        return phones

    @field_validator("Mobile", mode="before")
    @classmethod
    def extract_single_mobile(cls, mobiles: Any) -> Any:
        if isinstance(mobiles, list):
            return mobiles[0] if mobiles else ""
        return mobiles

    @model_validator(mode="after")
    def ensure_at_least_one_name(self) -> 'CustomerBillit':
        if not (self.Name or self.ContactFirstName or self.ContactLastName):
            raise SyncoraError("At least one of Name, ContactFirstName or ContactLastName must be provided", 900, Severity.HIGH)
        return self
