from typing import Any


class SyncoraDBClass:

    @staticmethod
    def get_one(item_id: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError

    @staticmethod
    def get(*args: list, **kwargs: dict) -> Any:  # noqa: ANN401
        raise NotImplementedError

    @staticmethod
    def create(item: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError

    @staticmethod
    def update(item_id: Any, item: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError

    @staticmethod
    def delete(item_id: Any) -> Any:  # noqa: ANN401
        raise NotImplementedError

    @staticmethod
    def contains(item_id: str | int) -> bool:
        raise NotImplementedError

    @staticmethod
    def size() -> int:
        raise NotImplementedError
