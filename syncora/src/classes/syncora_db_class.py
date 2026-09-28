from abc import ABC, abstractmethod
from typing import Any


class SyncoraDBClass[IdT, ItemT](ABC):

    @classmethod
    @abstractmethod
    def get_one(cls, item_id: IdT, /) -> ItemT:
        """Return the item identified by ``item_id``."""

    @classmethod
    @abstractmethod
    def get(
        cls,
        *args: Any,  # noqa: ANN401 # pyright: ignore[reportAny, reportExplicitAny]
        **kwargs: Any,  # noqa: ANN401 # pyright: ignore[reportAny, reportExplicitAny]
    ) -> object:
        """Return items; the signature is backend specific."""

    @classmethod
    @abstractmethod
    def create(cls, item: ItemT, /) -> IdT:
        """Store ``item`` and return its id."""

    @classmethod
    @abstractmethod
    def update(cls, item_id: IdT, item: ItemT, /) -> object:
        """Update the item identified by ``item_id``."""

    @classmethod
    @abstractmethod
    def delete(cls, item_id: IdT, /) -> object:
        """Delete the item identified by ``item_id``."""

    @classmethod
    @abstractmethod
    def contains(cls, item_id: IdT, /) -> bool:
        """Return whether an item identified by ``item_id`` exists."""

    @classmethod
    def size(cls) -> int:
        """Return the number of stored items."""
        raise NotImplementedError
