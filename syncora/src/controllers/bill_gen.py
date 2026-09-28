import io
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader
from pypdf import PdfWriter
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from dto.pdf import PDF
from pdf.static_data import bill_static

if TYPE_CHECKING:
    from dto.back import BillBack, CustomerBack


def create_bill_pdf(order_data: BillBack, customer_data: CustomerBack) -> bytes:
    language = customer_data.language.upper()
    static_data = bill_static[language]
    order, order_lines = order_data.to_pdf()
    dyn_data = PDF(
        Order=order,
        Customer=customer_data.to_pdf(),
        OrderLines=order_lines,
    )
    return bill_gen(static_data, dyn_data)


def html_to_pdf(html_content: str) -> bytes:
    font_config = FontConfiguration()
    css = CSS("./src/pdf/pdf.css", font_config=font_config)

    pdf_bytes: bytes = (
        HTML(string=html_content).write_pdf(stylesheets=[css], font_config=font_config)
        or b""
    )

    merger = PdfWriter()
    merger.append(io.BytesIO(pdf_bytes))
    merger.append("./src/pdf/verkoopsvoorwaarden.pdf")

    output = io.BytesIO()
    _ = merger.write(output)
    merger.close()

    return output.getvalue()


def bill_gen(static_data: dict[str, Any], dyn_data: PDF) -> bytes:
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
