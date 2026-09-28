from typing import TypedDict


class OrderLinePDF(TypedDict):
    Description: str
    AmountExcl: str
    Quantity: str
    Unit: str
    TotalExcl: str
    VATPercentage: str
    TotalIncl: str
