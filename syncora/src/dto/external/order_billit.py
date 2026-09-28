from pydantic import BaseModel, Field, computed_field

from constants.billit import (
    ORDER_DIRECTION_INCOME,
    ORDER_TYPE_CREDIT_NOTE,
    ORDER_TYPE_INVOICE,
)

from .billit_pdf import BillitPDF  # noqa: TC001
from .customer_billit import CustomerBillit  # noqa: TC001
from .order_line_billit import OrderLineBillit  # noqa: TC001


class OrderBillit(BaseModel):
    Customer: CustomerBillit = Field(frozen=True)
    OrderNumber: str = Field(validation_alias="orderNumber", frozen=True)
    OrderDate: str = Field(validation_alias="orderDate", frozen=True)
    ExpiryDate: str = Field(validation_alias="expiryDate", frozen=True)
    DeliveryDate: str | None = Field(
        default=None, validation_alias="deliveryDate", frozen=True
    )
    OrderTitle: str = Field(validation_alias="orderTitle", frozen=True)
    OrderLines: list[OrderLineBillit] = Field(
        validation_alias="orderLines", frozen=True
    )
    VentilationCode: str = Field(validation_alias="ventilationCode", frozen=True)
    TotalExcl: float = Field(validation_alias="total_excl", frozen=True)
    TotalIncl: float = Field(validation_alias="total_incl", frozen=True)
    TotalVAT: float = Field(validation_alias="total_vat", frozen=True)
    AboutInvoiceNumber: str | None = Field(
        default=None, validation_alias="aboutInvoiceNumber", frozen=True
    )
    PaymentReference: str = "+++564/5621/00034+++"
    OrderPDF: BillitPDF

    @computed_field
    def OrderType(self) -> str:  # noqa: N802
        return ORDER_TYPE_CREDIT_NOTE if self.AboutInvoiceNumber else ORDER_TYPE_INVOICE

    @computed_field
    def OrderDirection(self) -> str:  # noqa: N802
        return ORDER_DIRECTION_INCOME
