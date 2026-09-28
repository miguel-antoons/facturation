def order_line_total_excl(quantity: float, unit_price_excl: float) -> float:
    return quantity * unit_price_excl


def order_line_total_incl(
    quantity: float, unit_price_excl: float, vat_percentage: float
) -> float:
    total_excl = order_line_total_excl(quantity, unit_price_excl)
    vat_amount = total_excl * vat_percentage / 100
    return total_excl + vat_amount
