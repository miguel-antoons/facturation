from typing import TypedDict


class OrderPDF(TypedDict):
    OrderNumber: str
    OrderDate: str
    ExpiryDate: str
    OrderTitle: str
    YourReference: str
    VAT: str
    TotalExcl: str
    TotalVAT: str
    TotalIncl: str
    Comments: str
    VentilationCode: str
