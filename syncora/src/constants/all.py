import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, NotRequired, Self, TypedDict

from pydantic import BaseModel, model_serializer
from pydantic_core import core_schema

if TYPE_CHECKING:
    from pydantic_core.core_schema import SerializerFunctionWrapHandler


RESPONSE_SUCCESS = "success"
RESPONSE_ERROR = "error"
RESPONSE_WARNING = "warning"
COUNTRY_CODE_BE = "BE"


class ResponseMessage(TypedDict):
    id: NotRequired[int | str]
    status: str
    message: NotRequired[str]
    code: NotRequired[int]


class Undefined:
    _instance = None

    def __new__(cls, *args: list, **kwargs: dict) -> Self:
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Any  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        return core_schema.any_schema()

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:  # noqa: ANN401
        return self is other

    def __ne__(self, other: object) -> bool:  # noqa: ANN401
        return self is not other

    def __le__(self, other: Any) -> bool:  # noqa: ANN401
        raise NotImplementedError

    def __gt__(self, other: Any) -> bool:  # noqa: ANN401
        raise NotImplementedError

    def __ge__(self, other: Any) -> bool:  # noqa: ANN401
        raise NotImplementedError

    def __lt__(self, other: Any) -> bool:  # noqa: ANN401
        raise NotImplementedError

    def __hash__(self) -> int:
        raise NotImplementedError


SyncoraUndefined = Undefined()


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

    @staticmethod
    @abstractmethod
    def from_db(*args: list, **kwargs: dict) -> SyncoraModel:
        pass

    @abstractmethod
    def to_db(self) -> dict:
        pass

    @abstractmethod
    def to_front(self) -> str | dict:
        pass
