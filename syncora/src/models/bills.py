from models.order_model import OrderModel
from src.constants.bill_back import BillBack


class BillModel(OrderModel[BillBack]):
    database_name = "bills"
    UsedDTO = BillBack
