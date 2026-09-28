from typing import NotRequired, TypedDict


class ResponseMessage(TypedDict):
    id: NotRequired[int | str]
    status: str
    message: NotRequired[str]
    code: NotRequired[int]
