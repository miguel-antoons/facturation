from typing import Annotated, NotRequired, ReadOnly, TypedDict


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
