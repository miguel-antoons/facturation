from typing import TypedDict, NotRequired


RESPONSE_SUCCESS = "success"
RESPONSE_ERROR = "error"
RESPONSE_WARNING = "warning"
COUNTRY_CODE_BE = "BE"


class ResponseMessage(TypedDict):
    id: NotRequired[int | str]
    status: str
    message: NotRequired[str]
    code: NotRequired[int]
