from typing import NotRequired, ReadOnly, TypedDict

from constants.customer_fields import (
    CUSTOMER_DB_ADDRESS,
    CUSTOMER_DB_ARCHITECT_NAME,
    CUSTOMER_DB_CITY,
    CUSTOMER_DB_COMMENT,
    CUSTOMER_DB_COMPANY,
    CUSTOMER_DB_FIRSTNAME,
    CUSTOMER_DB_ID,
    CUSTOMER_DB_LANGUAGE,
    CUSTOMER_DB_NAME,
    CUSTOMER_DB_POSTAL_CODE,
    CUSTOMER_DB_SALUTATION,
    CUSTOMER_DB_VAT_NUMBER,
)

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
