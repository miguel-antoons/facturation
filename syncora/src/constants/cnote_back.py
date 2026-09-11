from pydantic import Field

from src.constants.order_back import OrderBack


class CnoteBack(OrderBack):
    aboutInvoiceNumber: str = Field(default=None)  # noqa: N815
