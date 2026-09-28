from typing import Any, Self

from pydantic_core import core_schema


class Undefined:
    """Sentinel marking a field that was never provided (distinct from ``None``).

    The backend relies on this distinction -- e.g. ``is_cnote`` checks whether
    ``aboutInvoiceNumber`` is an ``Undefined`` value, and ``SyncoraModel``
    serialization drops ``Undefined``-valued fields from its output. It is a
    singleton so identity comparisons (``is``) and ``__eq__`` agree, and it is
    falsy so ``if not value`` treats "not provided" like emptiness.
    """

    _instance = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
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
