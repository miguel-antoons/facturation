from constants.cnote_back import CnoteBack
from models.order_model import OrderModel


class CnoteModel(OrderModel[CnoteBack]):
    database_name = "cnotes"
    UsedDTO = CnoteBack
