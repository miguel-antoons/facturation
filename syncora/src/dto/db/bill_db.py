from .order_db import OrderDB


class BillDB(OrderDB):
    deliveryDate: str  # noqa: N815
