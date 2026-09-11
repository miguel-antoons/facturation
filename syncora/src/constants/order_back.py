from typing import Any, NotRequired, Self, TypedDict

from bson import ObjectId
from pydantic import BaseModel, Field, computed_field, field_validator

from constants.all import SyncoraModel, SyncoraUndefined, Undefined
from src.utils.date_formatter import format_date
from utils.generic_error import Severity, SyncoraError

PEPPOL_DELIVERY_STATUS_NOT_SENT = -1
PEPPOL_DELIVERY_STATUS_UNKNOWN = 0
PEPPOL_DELIVERY_STATUS_PENDING = 1
PEPPOL_DELIVERY_STATUS_SENT = 2

ORDER_BACK_EXTERNAL_ID = "externalId"
ORDER_BACK_PEPPOL_DELIVERY_STATUS = "peppolDeliveryStatus"
ORDER_BACK_ORDER_NUMBER = "orderNumber"

ORDER_BACK_DEFAULT_EXTERNAL_ID = 0


# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR DATABASE
# * ------------------------------------------
class OrderLineDB(TypedDict):
    description: str
    quantity: float | int
    unitPriceExcl: float
    unit: str
    VATPercentage: float


class OrderDB(TypedDict):
    _id: NotRequired[str]
    orderId: NotRequired[int]
    customerId: NotRequired[int]
    orderNumber: str
    orderDate: str
    expiryDate: str
    deliveryDate: str
    orderTitle: str
    orderLines: NotRequired[list[OrderLineDB]]
    ventilationCode: NotRequired[str]
    aboutInvoiceNumber: NotRequired[str]
    peppolDeliveryStatus: NotRequired[int]


class _OrderLineBack(BaseModel):
    description: str = Field(default="")  # noqa: N815
    quantity: float | int = Field(default=1)
    unitPriceExcl: float = Field(default=0.00)  # noqa: N815
    unit: str = Field(default="")
    VATPercentage: float = Field(default=0)  # noqa: N815

    @computed_field(alias="TotalExcl")
    @property
    def total_excl(self) -> float:
        return round(_order_line_total_excl(self.quantity, self.unitPriceExcl), 2)

    @computed_field(alias="TotalIncl")
    @property
    def total_incl(self) -> float:
        return round(
            _order_line_total_incl(
                self.quantity, self.unitPriceExcl, self.VATPercentage
            ),
            2,
        )

    @computed_field(alias="TotalVAT")
    @property
    def total_vat(self) -> float:
        return self.total_incl - self.total_excl


def _order_line_total_excl(quantity: float, unit_price_excl: float) -> float:
    return quantity * unit_price_excl


def _order_line_total_incl(
    quantity: float, unit_price_excl: float, vat_percentage: float
) -> float:
    total_excl = _order_line_total_excl(quantity, unit_price_excl)
    vat_amount = total_excl * vat_percentage / 100
    return total_excl + vat_amount


class OrderBack(SyncoraModel):
    orderId: str = Field(default=SyncoraUndefined, validation_alias="_id")  # noqa: N815
    customerId: int = Field(default=SyncoraUndefined)  # noqa: N815
    customerName: str = Field(default=SyncoraUndefined)  # noqa: N815
    externalId: int = Field(default=SyncoraUndefined)  # noqa: N815
    orderNumber: str = Field(default=SyncoraUndefined)  # noqa: N815
    orderDate: str = Field(default=SyncoraUndefined)  # noqa: N815
    orderTitle: str = Field(default=SyncoraUndefined)  # noqa: N815
    orderLines: list[_OrderLineBack] = Field(default=[])  # noqa: N815
    expiryDate: str = Field(default=SyncoraUndefined)  # noqa: N815
    deliveryDate: str = Field(default=SyncoraUndefined)  # noqa: N815
    ventilationCode: str = Field(default=SyncoraUndefined)  # noqa: N815
    aboutInvoiceNumber: str = Field(default=SyncoraUndefined)  # noqa: N815
    peppolDeliveryStatus: int = Field(default=SyncoraUndefined)  # noqa: N815
    _total_excl: float = None
    _total_incl: float = None

    @computed_field(alias="billitSent")
    @property
    def billit_sent(self) -> bool:
        return self.ret_def(
            self.externalId, bool(self.externalId) and self.externalId > 0
        )

    @computed_field(alias="totalExcl")
    @property
    def total_excl(self) -> float:
        if not self._total_excl:
            self._calc_totals()
        if self._total_excl < 0:
            raise SyncoraError(
                "Calculated Total Excl has negative value", 903, Severity.HIGH
            )
        return self._total_excl

    @computed_field(alias="totalIncl")
    @property
    def total_incl(self) -> float:
        if not self._total_incl:
            self._calc_totals()
        if self._total_incl < 0:
            raise SyncoraError(
                "Calculated Total Incl has negative value", 904, Severity.HIGH
            )
        return self._total_incl

    @computed_field(alias="totalVAT")
    @property
    def total_vat(self) -> float:
        if not self._total_incl or not self._total_excl:
            self._calc_totals()
        res = self._total_incl - self._total_excl
        if res < 0:
            raise SyncoraError(
                "Calculated Total VAT has negative value", 905, Severity.HIGH
            )
        return round(res, 2)

    @property
    def locked(self) -> bool:
        if isinstance(self.billit_sent, Undefined):
            raise SyncoraError(
                "Could not determine locked status as the 'externalId' "
                "property was not given.",
                906,
                Severity.MEDIUM,
            )
        return self.billit_sent

    @property
    def undeletable(self) -> bool:
        if isinstance(self.peppolDeliveryStatus, Undefined):
            raise SyncoraError(
                "Could not determine undeletable status as the "
                "'peppolDeliveryStatus' property was not given.",
                906,
                Severity.MEDIUM,
            )
        return self.peppolDeliveryStatus != PEPPOL_DELIVERY_STATUS_NOT_SENT

    @property
    def formatted_order_date(self) -> str:
        return format_date(self.orderDate)

    @property
    def formatted_expiry_date(self) -> str:
        return format_date(self.expiryDate)

    @field_validator("orderId", mode="before")
    @classmethod
    def order_id(cls, order_id: Any) -> Any:  # noqa: ANN401
        if isinstance(order_id, ObjectId):
            return str(order_id)
        return order_id

    @classmethod
    def from_db(cls, order_db: OrderDB) -> Self:
        return cls.model_validate(order_db)

    def to_db(self) -> OrderDB:
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

    def _calc_totals(self) -> None:
        """Compute order totals using Billit's taxable-amount method.

        Lines are grouped by VAT rate; the unrounded excl amount is summed per
        group, VAT is applied per group, and rounding happens once at the end.
        This matches how Billit recalculates totals server-side (see the Billit
        "Calculation Method" docs) and avoids the rounding drift that the
        per-line method accumulates. Per-line totals (shown individually on the
        PDF) are unaffected and remain line-rounded.
        """
        total_excl = 0.0
        # Unrounded excl amount accumulated per VAT rate.
        excl_by_rate: dict[float, float] = {}

        for line in self.orderLines:
            line_excl = line.quantity * line.unitPriceExcl
            total_excl += line_excl
            excl_by_rate[line.VATPercentage] = (
                excl_by_rate.get(line.VATPercentage, 0.0) + line_excl
            )

        total_incl = sum(
            round(group_excl * (1 + rate / 100), 2)
            for rate, group_excl in excl_by_rate.items()
        )

        self._total_excl = round(total_excl, 2)
        self._total_incl = total_incl
