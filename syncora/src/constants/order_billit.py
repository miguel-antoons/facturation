from typing import TypedDict

from pydantic import BaseModel, Field, computed_field, field_validator

from constants.customer_billit import CustomerBillit
from utils.generic_error import SyncoraError, Severity

ORDER_TYPE_INVOICE = "Invoice"
ORDER_TYPE_CREDIT_NOTE = "CreditNote"
ORDER_DIRECTION_INCOME = "Income"



# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR BILLIT API
# * ------------------------------------------

class BillitPDF(TypedDict):
    FileName: str
    FileContent: str


class OrderLinesBillit(BaseModel):
    Description: str = Field(validation_alias="description", frozen=True)
    Quantity: float | int = Field(validation_alias="quantity", frozen=True)
    UnitPriceExcl: float = Field(validation_alias="unitPriceExcl", frozen=True)
    Unit: str = Field(validation_alias="unit", frozen=True)
    VATPercentage: float = Field(validation_alias="VATPercentage", frozen=True)
    TotalExcl: float = Field(validation_alias="total_excl", frozen=True)
    TotalIncl: float = Field(validation_alias="total_incl", frozen=True)
    TotalVAT: float = Field(validation_alias="total_vat", frozen=True)


    @field_validator("Description", mode="after")
    @classmethod
    def non_empty_description(cls, description: str) -> str:
        if not description:
            raise SyncoraError("Order line description cannot be empty", 901, severity=Severity.HIGH)
        return description


class OrderBillit(BaseModel):
    Customer: CustomerBillit = Field(frozen=True)
    OrderNumber: str = Field(validation_alias="orderNumber", frozen=True)
    OrderDate: str = Field(validation_alias="orderDate", frozen=True)
    ExpiryDate: str = Field(validation_alias="expiryDate", frozen=True)
    DeliveryDate: str | None = Field(default=None, validation_alias="deliveryDate", frozen=True)
    OrderTitle: str = Field(validation_alias="orderTitle", frozen=True)
    OrderLines: list[OrderLinesBillit] = Field(validation_alias="orderLines", frozen=True)
    VentilationCode: str = Field(validation_alias="ventilationCode", frozen=True)
    TotalExcl: float = Field(validation_alias="total_excl", frozen=True)
    TotalIncl: float = Field(validation_alias="total_incl", frozen=True)
    TotalVAT: float = Field(validation_alias="total_vat", frozen=True)
    AboutInvoiceNumber: str | None = Field(default=None, validation_alias="aboutInvoiceNumber", frozen=True)
    OrderPDF: BillitPDF


    @computed_field
    def OrderType(self) -> str:
        return ORDER_TYPE_CREDIT_NOTE if self.AboutInvoiceNumber else ORDER_TYPE_INVOICE


    @computed_field
    def OrderDirection(self) -> str:
        return ORDER_DIRECTION_INCOME
