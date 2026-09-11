from src.constants.order_back import OrderBack
from src.utils.date_formatter import format_date


class BillBack(OrderBack):
    @property
    def ogm(self) -> str:
        ref_numbers = self.orderNumber.ljust(10, "0")
        check_digit = int(ref_numbers[:10]) % 97
        if check_digit == 0:
            check_digit = 97
        return (
            f"+++{ref_numbers[0:3]}/{ref_numbers[3:7]}/"
            f"{ref_numbers[7:10]}{str(check_digit).ljust(2, '0')}+++"
        )

    @property
    def formatted_delivery_date(self) -> str:
        return format_date(self.deliveryDate)
