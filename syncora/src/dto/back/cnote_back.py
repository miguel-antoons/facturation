from typing import TYPE_CHECKING, Any, Self

from pydantic import Field

from classes import SyncoraUndefined
from dto.pdf import CnotePDF, OrderLinePDF
from utils.formatters import order_line_string, price_to_string

from .order_back import OrderBack

if TYPE_CHECKING:
    from dto.db import CnoteDB


class CnoteBack(OrderBack):
    aboutInvoiceNumber: str = Field(default=SyncoraUndefined)  # noqa: N815

    @classmethod
    def from_db(cls, order_db: CnoteDB) -> Self:
        return cls.model_validate(order_db)

    def to_db(self) -> CnoteDB:
        return self.model_dump(
            exclude_unset=True, exclude_computed_fields=True, exclude={"orderId"}
        )

    def to_front(self) -> dict[str, Any]:  # noqa: ANN401
        return self.model_dump(
            exclude={
                "orderId": True,
                "externalId": True,
                "total_excl": True,
                "total_incl": True,
                "total_vat": True,
                "orderLines": {
                    "__all__": {
                        "total_excl",
                        "total_incl",
                        "total_vat",
                    }
                },
            },
            by_alias=True,
        )

    def to_pdf(self) -> tuple[CnotePDF, list[OrderLinePDF]]:
        return (
            CnotePDF(
                OrderNumber=self.orderNumber,
                AboutInvoiceNumber=self.aboutInvoiceNumber or "",
                OrderDate=self.formatted_order_date,
                ExpiryDate=self.formatted_expiry_date,
                OrderTitle=self.orderTitle,
                YourReference=self.orderNumber,
                VAT=price_to_string(self.orderLines[0].VATPercentage),
                TotalExcl=price_to_string(self.total_excl),
                TotalVAT=price_to_string(self.total_vat),
                TotalIncl=price_to_string(self.total_incl),
                Comments="",
                VentilationCode=self.ventilationCode or "",
            ),
            list(map(order_line_string, self.orderLines)),
        )
