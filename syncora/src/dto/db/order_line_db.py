from typing import TypedDict


class OrderLineDB(TypedDict):
    description: str
    quantity: float | int
    unitPriceExcl: float
    unit: str
    VATPercentage: float
