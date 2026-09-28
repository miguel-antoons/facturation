from typing import ClassVar

from dto.back import BillBack
from models.order_model import OrderModel


class BillModel(OrderModel[BillBack]):
    database_name: ClassVar[str] = "bills"
    UsedDTO: type[BillBack] = BillBack
