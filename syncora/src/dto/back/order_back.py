from abc import ABC
from typing import Any

from bson import ObjectId
from pydantic import Field, computed_field, field_validator

from classes import SyncoraModel, SyncoraUndefined, Undefined
from constants.peppol import PEPPOL_DELIVERY_STATUS_NOT_SENT
from utils.formatters import format_date
from utils.generic_error import Severity, SyncoraError

from .order_line_back import OrderLineBack  # noqa: TC001


class OrderBack[DbT, PdfT](SyncoraModel[DbT, dict[str, Any], PdfT], ABC):
    orderId: str = Field(default=SyncoraUndefined, validation_alias="_id")
    customerId: int = Field(default=SyncoraUndefined)
    customerName: str = Field(default=SyncoraUndefined)
    externalId: int = Field(default=SyncoraUndefined)
    orderNumber: str = Field(default=SyncoraUndefined)
    orderDate: str = Field(default=SyncoraUndefined)
    orderTitle: str = Field(default=SyncoraUndefined)
    orderLines: list[OrderLineBack] = Field(default=[])
    expiryDate: str = Field(default=SyncoraUndefined)
    ventilationCode: str = Field(default=SyncoraUndefined)
    peppolDeliveryStatus: int = Field(default=SyncoraUndefined)
    _total_excl: float = None
    _total_incl: float = None

    @computed_field(alias="billitSent")
    @property
    def billit_sent(self) -> bool | Undefined:
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
