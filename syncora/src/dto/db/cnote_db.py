from typing import NotRequired

from .order_db import OrderDB


class CnoteDB(OrderDB):
    aboutInvoiceNumber: NotRequired[str]  # noqa: N815
