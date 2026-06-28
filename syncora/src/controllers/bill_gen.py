import io
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader
from PyPDF2 import PdfMerger
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from constants.order_pdf import PDF, order_line_string, price_to_string
from controllers.billit import format_dyn_data
from pdf.static_data import bill_static_fr, bill_static_nl, six_percent_certificate

if TYPE_CHECKING:
    from constants.customer_back import CustomerBack
    from constants.order_back import OrderBack


def create_bill(order_data: OrderBack, customer_data: CustomerBack) -> bytes:
    if customer_data.language.upper() == "FR":
        return fr_bill(order_data, customer_data)
    return nl_bill(order_data, customer_data)


def nl_bill(order_data: OrderBack, customer_data: CustomerBack) -> bytes:
    static_data = bill_static_nl()
    static_data["Label"]["SixPercentVatCertificate"] = (
        six_percent_certificate["NL"] if order_data.ventilationCode == "2" else ""
    )
    dyn_data = format_dyn_data(
        order_data,
        customer_data,
        set_id=True,
        number_formatter=price_to_string,
        order_lines_formater=order_line_string,
    )
    return bill_gen(static_data, dyn_data)


def fr_bill(order_data: OrderBack, customer_data: CustomerBack) -> bytes:
    static_data = bill_static_fr()
    static_data["Label"]["SixPercentVatCertificate"] = (
        six_percent_certificate["FR"] if order_data.ventilationCode == "2" else ""
    )
    dyn_data = format_dyn_data(
        order_data,
        customer_data,
        set_id=True,
        number_formatter=price_to_string,
        order_lines_formater=order_line_string,
    )
    return bill_gen(static_data, dyn_data)


def html_to_pdf(html_content: str) -> bytes:
    font_config = FontConfiguration()
    css = CSS("./src/pdf/pdf.css", font_config=font_config)

    pdf_bytes = HTML(string=html_content).write_pdf(
        stylesheets=[css], font_config=font_config
    )

    merger = PdfMerger()
    merger.append(io.BytesIO(pdf_bytes))
    merger.append("./src/pdf/verkoopsvoorwaarden.pdf")

    output = io.BytesIO()
    merger.write(output)
    merger.close()

    return output.getvalue()


def bill_gen(static_data: dict[str, dict[str, str]], dyn_data: PDF) -> bytes:
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader("src/pdf/templates"), autoescape=True)
    bill_template = env.get_template("bill_template.html")

    unit_is_empty = all(line["Unit"] == "" for line in dyn_data["OrderLines"])
    add_salutation = (
        dyn_data["Customer"]["Salutation"] != ""
        and dyn_data["Customer"]["ContactFullName"] != ""
    )

    html_content = bill_template.render(
        static_data=static_data,
        dyn_data=dyn_data,
        unit_is_empty=unit_is_empty,
        add_salutation=add_salutation,
    )
    return html_to_pdf(html_content)
