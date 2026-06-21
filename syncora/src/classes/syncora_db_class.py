from typing import Any


class SyncoraDBClass:

    @staticmethod
    def get_one(item_id: Any):
        raise NotImplementedError

    @staticmethod
    def get(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def create(item: Any):
        raise NotImplementedError

    @staticmethod
    def update(item_id: Any, item: Any):
        raise NotImplementedError

    @staticmethod
    def delete(item_id: Any):
        raise NotImplementedError

    @staticmethod
    def contains(item_id: str | int) -> bool:
        raise NotImplementedError

    @staticmethod
    def size():
        raise NotImplementedError
