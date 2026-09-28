from typing import TypedDict


class OrderLineFront(TypedDict):
    description: str
    quantity: float
    unitPriceExcl: float
    unit: str
    VATPercentage: float
