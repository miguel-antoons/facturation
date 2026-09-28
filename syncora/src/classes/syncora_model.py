import warnings
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, SerializerFunctionWrapHandler, model_serializer

from classes.undefined import Undefined


class SyncoraModel(BaseModel, ABC):
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
    def ret_def(val: Any, alt: Any) -> Any:  # noqa: ANN401
        return val if isinstance(val, Undefined) else alt

    @classmethod
    @abstractmethod
    def from_db(cls, *args: list, **kwargs: dict) -> SyncoraModel:
        pass

    @abstractmethod
    def to_db(self) -> dict:
        pass

    @abstractmethod
    def to_front(self) -> str | dict:
        pass

    @abstractmethod
    def to_pdf(self) -> dict:
        pass
