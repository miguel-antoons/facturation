from models.order_model import OrderModel
from src.constants.cnote_back import CnoteBack


class CnoteModel(OrderModel[CnoteBack]):
    database_name = "cnotes"
    UsedDTO = CnoteBack
