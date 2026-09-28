from typing import Any, Self, override

from pydantic import Field, field_validator

from classes import SyncoraUndefined
from dto.db import BillDB
from dto.pdf import BillPDF, OrderLinePDF
from utils.formatters import format_date, order_line_string, price_to_string

from .order_back import OrderBack


class BillBack(OrderBack[BillDB, tuple[BillPDF, list[OrderLinePDF]]]):
    deliveryDate: str = Field(default=SyncoraUndefined)

    @field_validator("orderNumber")
    @classmethod
    def order_number_only_digits(cls, value: str) -> str:
        if value and not value.isdigit():
            raise ValueError(
                "orderNumber must contain only numerical digits, " f"got '{value}'"
            )
        return value

    @property
    def ogm(self) -> str:
        ref_numbers = self.orderNumber.ljust(10, "0")
        check_digit = int(ref_numbers[:10]) % 97
        if check_digit == 0:
            check_digit = 97
        return (
            f"+++{ref_numbers[0:3]}/{ref_numbers[3:7]}/"
            f"{ref_numbers[7:10]}{str(check_digit).ljust(2, '0')}+++"
        )

    @property
    def formatted_delivery_date(self) -> str:
        return format_date(self.deliveryDate)

    @classmethod
    @override
    def from_db(cls, order_db: BillDB) -> Self:
        return cls.model_validate(order_db)

    @override
    def to_db(self) -> BillDB:
        return BillDB(
            **self.model_dump(  # pyright: ignore[reportAny]
                exclude_unset=True,
                exclude_computed_fields=True,
                exclude={"orderId"},
            )
        )

    @override
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

    @override
    def to_pdf(self) -> tuple[BillPDF, list[OrderLinePDF]]:
        return (
            BillPDF(
                OrderNumber=self.orderNumber,
                OrderDate=self.formatted_order_date,
                DeliveryDate=self.formatted_delivery_date,
                ExpiryDate=self.formatted_expiry_date,
                OrderTitle=self.orderTitle,
                YourReference=self.orderNumber,
                VAT=price_to_string(self.orderLines[0].VATPercentage),
                TotalExcl=price_to_string(self.total_excl),
                TotalVAT=price_to_string(self.total_vat),
                TotalIncl=price_to_string(self.total_incl),
                Comments="",
                VentilationCode=self.ventilationCode,
                OGM=self.ogm,
            ),
            list(map(order_line_string, self.orderLines)),
        )
