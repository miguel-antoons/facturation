from pydantic import BaseModel, Field, field_validator

from utils.generic_error import Severity, SyncoraError


class OrderLineBillit(BaseModel):
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
            raise SyncoraError(
                "Order line description cannot be empty", 901, severity=Severity.HIGH
            )
        return description
