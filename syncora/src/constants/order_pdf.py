from typing import NotRequired, TypedDict


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR PDF GENERATION
# * ------------------------------------------
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


class BillPDF(OrderPDF):
    DeliveryDate: str
    OGM: str


class CnotePDF(OrderPDF):
    AboutInvoiceNumber: str


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


class OrderLinePDF(TypedDict):
    Description: str
    AmountExcl: str
    Quantity: str
    Unit: str
    TotalExcl: str
    VATPercentage: str
    TotalIncl: str


class PDF(TypedDict):
    id: NotRequired[str]
    Order: OrderPDF
    Customer: CustomerPDF
    OrderLines: list[OrderLinePDF]
