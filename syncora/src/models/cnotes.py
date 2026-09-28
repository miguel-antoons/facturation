from typing import ClassVar

from dto.back import CnoteBack
from models.order_model import OrderModel


class CnoteModel(OrderModel[CnoteBack]):
    database_name: ClassVar[str] = "cnotes"
    UsedDTO: type[CnoteBack] = CnoteBack
