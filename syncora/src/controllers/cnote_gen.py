from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader

from constants.order_pdf import PDF
from controllers.bill_gen import html_to_pdf
from pdf.static_data import cnote_static

if TYPE_CHECKING:
    from constants.cnote_back import CnoteBack
    from constants.customer_back import CustomerBack


def create_cnote_pdf(order_data: CnoteBack, customer_data: CustomerBack) -> bytes:
    language = customer_data.language.upper()
    static_data = cnote_static[language]
    order, order_lines = order_data.to_pdf()
    dyn_data = PDF(
        Order=order,
        Customer=customer_data.to_pdf(),
        OrderLines=order_lines,
    )
    return cnote_gen(static_data, dyn_data)


def cnote_gen(static_data: dict[str, dict[str, str]], dyn_data: PDF) -> bytes:
    env = Environment(loader=FileSystemLoader("src/pdf/templates"), autoescape=True)
    cnote_template = env.get_template("cnote_template.html")

    unit_is_empty = all(line["Unit"] == "" for line in dyn_data["OrderLines"])
    add_salutation = (
        dyn_data["Customer"]["Salutation"] != ""
        and dyn_data["Customer"]["ContactFullName"] != ""
    )

    html_content = cnote_template.render(
        static_data=static_data,
        dyn_data=dyn_data,
        unit_is_empty=unit_is_empty,
        add_salutation=add_salutation,
    )
    return html_to_pdf(html_content)
