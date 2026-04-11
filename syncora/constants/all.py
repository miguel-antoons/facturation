from typing import TypedDict, NotRequired, Any
from abc import ABC, abstractmethod

from pydantic import model_serializer, BaseModel
from pydantic_core import core_schema

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

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        return core_schema.any_schema()

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __le__(self, other):
        raise NotImplementedError

    def __gt__(self, other):
        raise NotImplementedError

    def __ge__(self, other):
        raise NotImplementedError

    def __lt__(self, other):
        raise NotImplementedError

SyncoraUndefined = Undefined()


class SyncoraModel(BaseModel, ABC):
    @model_serializer(mode='wrap')
    def serialize_model(self, handler) -> dict[str, Any]:
        dumped = handler(self)
        return {k: v for k, v in dumped.items() if not isinstance(v, Undefined)}

    @staticmethod
    def ret_def(val: Any, alt: Any) -> Any:
        return val if isinstance(val, Undefined) else alt

    @staticmethod
    @abstractmethod
    def from_db(*args, **kwargs) -> "SyncoraModel":
        pass

    @abstractmethod
    def to_db(self) -> Any:
        pass

    @abstractmethod
    def to_front(self) -> str:
        pass
