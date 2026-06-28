from typing import Any, NotRequired, TypedDict

from bson import ObjectId
from dateutil import parser
from pydantic import BaseModel, Field, computed_field, field_validator

from constants.all import SyncoraModel, SyncoraUndefined, Undefined
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


def _format_date(date: str) -> str:
    return parser.parse(date).strftime("%d/%m/%Y") if date else ""


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
        return res

    @property
    def ogm(self) -> str:
        if self.is_cnote:
            return ""
        ref_numbers = self.orderNumber.ljust(10, "0")
        check_digit = int(ref_numbers[:10]) % 97
        if check_digit == 0:
            check_digit = 97
        return (
            f"+++{ref_numbers[0:3]}/{ref_numbers[3:7]}/"
            f"{ref_numbers[7:10]}{str(check_digit).ljust(2, '0')}+++"
        )

    @property
    def is_cnote(self) -> bool:
        return not isinstance(self.aboutInvoiceNumber, Undefined)

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
        return _format_date(self.orderDate)

    @property
    def formatted_delivery_date(self) -> str:
        if self.is_cnote:
            return ""
        return _format_date(self.deliveryDate)

    @property
    def formatted_expiry_date(self) -> str:
        return _format_date(self.expiryDate)

    @field_validator("orderId", mode="before")
    @classmethod
    def order_id(cls, order_id: Any) -> Any:  # noqa: ANN401
        if isinstance(order_id, ObjectId):
            return str(order_id)
        return order_id

    @staticmethod
    def from_db(order_db: OrderDB) -> OrderBack:
        return OrderBack.model_validate(order_db)

    def to_db(self) -> OrderDB:
        return self.model_dump(
            exclude_unset=True, exclude_computed_fields=True, exclude={"orderId"}
        )

    def to_front(self) -> str:
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
        total_excl = 0.0
        total_incl = 0.0

        for line in self.orderLines:
            total_excl += line.total_excl
            total_incl += line.total_incl

        self._total_excl = total_excl
        self._total_incl = total_incl
