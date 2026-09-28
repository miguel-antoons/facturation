import warnings
from abc import ABC, abstractmethod
from typing import Any, Self

from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer

from classes.undefined import Undefined


class SyncoraModel[  # pyright: ignore[reportUnsafeMultipleInheritance]
    DbT, FrontT, PdfT
](BaseModel, ABC):
    @model_serializer(mode="wrap")
    def serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Pydantic serializer warnings.*",
                category=UserWarning,
            )
            dumped = handler(self)
        return {k: v for k, v in dumped.items() if not isinstance(v, Undefined)}

    @staticmethod
    def ret_def[T, A](val: T, alt: A) -> Undefined | A:
        return val if isinstance(val, Undefined) else alt

    @classmethod
    @abstractmethod
    def from_db(cls, db: DbT, /) -> Self:
        """Build an instance from its raw database representation."""

    @abstractmethod
    def to_db(self) -> DbT:
        """Return the raw database representation of this model."""

    @abstractmethod
    def to_front(self) -> FrontT:
        """Return the frontend-facing representation of this model."""

    @abstractmethod
    def to_pdf(self) -> PdfT:
        """Return the PDF-facing representation of this model."""
