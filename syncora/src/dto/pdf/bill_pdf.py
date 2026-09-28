from .order_pdf import OrderPDF


class BillPDF(OrderPDF):
    DeliveryDate: str
    OGM: str
