from pydantic import BaseModel, Field, computed_field

from utils.prices import order_line_total_excl, order_line_total_incl


class OrderLineBack(BaseModel):
    description: str = Field(default="")  # noqa: N815
    quantity: float | int = Field(default=1)
    unitPriceExcl: float = Field(default=0.00)  # noqa: N815
    unit: str = Field(default="")
    VATPercentage: float = Field(default=0)  # noqa: N815

    @computed_field(alias="TotalExcl")
    @property
    def total_excl(self) -> float:
        return round(order_line_total_excl(self.quantity, self.unitPriceExcl), 2)

    @computed_field(alias="TotalIncl")
    @property
    def total_incl(self) -> float:
        return round(
            order_line_total_incl(
                self.quantity, self.unitPriceExcl, self.VATPercentage
            ),
            2,
        )

    @computed_field(alias="TotalVAT")
    @property
    def total_vat(self) -> float:
        return self.total_incl - self.total_excl
