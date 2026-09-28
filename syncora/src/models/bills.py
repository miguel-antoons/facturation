from dto.back import BillBack
from models.order_model import OrderModel


class BillModel(OrderModel[BillBack]):
    database_name = "bills"
    UsedDTO = BillBack
