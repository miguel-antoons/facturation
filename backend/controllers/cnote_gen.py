from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from PyPDF2 import PdfMerger
from pdf.static_data import *
from pdf.pdf_gen import format_dyn_data


def create_cnote(req_data: dict):
    if req_data["CounterParty"]["Language"].upper() == "FR":
        return fr_cnote(req_data)
    else:
        return nl_cnote(req_data)


def nl_cnote(req_data):
    static_data = cnote_static_nl()
    static_data["Label"]["SixPercentVatCertificate"] = six_percent_certificate["NL"] if req_data["VentilationCode"] == "2" else ""
    dyn_data = format_dyn_data(req_data)
    return cnote_gen(static_data, dyn_data)


def fr_cnote(req_data):
    static_data = cnote_static_fr()
    static_data["Label"]["SixPercentVatCertificate"] = six_percent_certificate["FR"] if req_data["VentilationCode"] == "2" else ""
    dyn_data = format_dyn_data(req_data)
    return cnote_gen(static_data, dyn_data)


def html_to_pdf(html_content, output_path):
    font_config = FontConfiguration()
    css = CSS("./pdf/pdf.css", font_config=font_config)
    HTML(string=html_content).write_pdf("/tmp/temp_cnote.pdf", stylesheets=[css], font_config=font_config)

    merger = PdfMerger()
    merger.append("/tmp/temp_cnote.pdf")
    merger.append("./pdf/verkoopsvoorwaarden.pdf")
    with open(output_path, "wb") as pdf_file:
        merger.write(pdf_file)
    merger.close()


def cnote_gen(static_data, dyn_data):
    unit_is_empty = all(line['Unit'] == "" for line in dyn_data['OrderLines'])

    order_string = ""
    for line in dyn_data['OrderLines']:
        price_is_not_zero = line['AmountExcl'] != "0,00"
        line_html = f"""
        <tr>
            <td class="align-left align-bottom">{line['Description'].replace("\n", "<br />").replace("/r", "")}</td>
            <td class="align-right align-bottom">{"€ " + line['AmountExcl'] if price_is_not_zero else ""}</td>
            <td class="align-right align-bottom">{line['Quantity']}</td>
            {"" if unit_is_empty else f"<td class =\"align-left align-bottom\">{line['Unit']}</td>"}
            <td class="align-right align-bottom">{"€ " + line['TotalExcl'] if price_is_not_zero else ""}</td>
            <td class="align-right align-bottom">{line['VATPercentage'] + " %" if price_is_not_zero else ""}</td>
            <td class="align-right align-bottom">{"€ " + line['TotalIncl'] if price_is_not_zero else ""}</td>
        </tr>
        """
        order_string += line_html

    html_content = f"""
    <html lang="en">
        <head>
            <meta charset="UTF-8" />
        </head>
        <body>
            <table cellpadding="1" cellspacing="0" class="header">
                <tbody>
                    <tr>
                      <td>
                        <div class="logo">{static_data["Me"]["Logo"]}</div>
                      </td>
                      <td>
                          <h1>{static_data["Label"]["OrderType"]}</h1>
                          <b>{static_data["Label"]["OrderNumber"]}:</b> {dyn_data["Order"]["OrderNumber"]}<br />
                          <b>{static_data["Label"]["AboutInvoiceNumber"]}:</b> {dyn_data["Order"]["AboutInvoiceNumber"]}
                      </td>
                    </tr>
                    <tr>
                        <td style="vertical-align: bottom;">
                            {static_data["Me"]["OfficialCompanyName"]}<br />
                            {static_data["Me"]["StreetAndNumber"]}<br />
                            {static_data["Me"]["ZipCode"]} {static_data["Me"]["City"]}<br />
                            {static_data["Me"]["CountryName"]}
                            <div>{static_data["Me"]["VAT"]}</div>
                        </td>
                        <td style="vertical-align: bottom;">
                            <div>{dyn_data["Customer"]["OfficialCompanyName"]}</div>
                            <div>{dyn_data["Customer"]["ContactFullName"]}</div>
                            {dyn_data["Customer"]["StreetAndNumber"]}<br />
                            {dyn_data["Customer"]["ZipCode"]} {dyn_data["Customer"]["City"]}<br />
                            {dyn_data["Customer"]["CountryName"]}
                            <div>{dyn_data["Customer"]["VAT"]}</div>
                        </td>
                    </tr>
                </tbody>
            </table>
            <!-- COMPANY DETAILS END --><!-- INVOICE DATA START -->

            <table cellpadding="1" cellspacing="0" class="details">
                <tbody>
                    <tr>
                        <td style="width: 20%;">
                            <b>{static_data["Label"]["Date"]}:<br />
                            {static_data["Label"]["ExpiryDate"]}: </b>
                        </td>
                        <td style="width: 30%;">
                            {dyn_data["Order"]["OrderDate"]}<br />
                            {dyn_data["Order"]["ExpiryDate"]}
                        </td>
                        <td colspan="2" style="width: 50%;">
                            <div><b>{static_data["Label"]["CustomerNumber"]}:</b> {dyn_data["Customer"]["Nr"]}<br />
                            <b>{static_data["Label"]["Re"]}:&nbsp;</b>{dyn_data["Order"]["Title"]}<br />
                            <strong>{static_data["Label"]["YourReference"]}:&nbsp;</strong>{dyn_data["Order"]["YourReference"]}</div>
                        </td>
                    </tr>
                </tbody>
            </table>
            <!-- INVOICE DATA END --><!-- INVOICE ITEMS START -->

            <div class="content">
                <table cellpadding="1" cellspacing="0" class="list">
                    <thead class="headerGroup">
                        <tr>
                            <th class="align-left">{static_data["Label"]["Description"]}</th>
                            <th class="align-right" style="width: 12%;">{static_data["Label"]["UnitPrice"]}</th>
                            <th class="align-right" style="width: 8%;">{static_data["Label"]["Count"]}</th>
                            {"" if unit_is_empty else f"<th class=\"align-left\" style=\"width: 8%;\">{static_data["Label"]["Unit"]}</th>"}
                            <th class="align-right" style="width: 12%;">{static_data["Label"]["Excl"]}</th>
                            <th class="align-right" style="width: 6%;">{static_data["Label"]["VAT"]}</th>
                            <th class="align-right" style="width: 12%;">{static_data["Label"]["Incl"]}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {order_string}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <table cellpadding="1" cellspacing="0" class="list">
                    <tfoot>
                        <tr>
                            <td class="sum align-right">&nbsp;</td>
                            <td class="sum align-right" style="width: 14%;"><br />
                            <strong>{dyn_data["Order"]["VAT"]}% {static_data["Label"]["VAT"]}</strong></td>
                            <td class="sum align-right" style="width: 14%;"><br />
                            <strong>{static_data["Label"]["Total"]}</strong></td>
                        </tr>
                        <tr>
                            <td class="sum middle align-right"><strong>{static_data["Label"]["Excl"]} {static_data["Label"]["VAT"]}</strong></td>
                            <td class="sum middle align-right">&nbsp;</td>
                            <td class="sum middle align-right">€ {dyn_data["Order"]["TotalExcl"]}</td>
                        </tr>
                        <tr>
                            <td class="sum middle align-right"><strong>{static_data["Label"]["VAT"]}</strong></td>
                            <td class="sum middle align-right">&nbsp;</td>
                            <td class="sum middle align-right">€ {dyn_data["Order"]["TotalVAT"]}</td>
                        </tr>
                        <tr>
                            <td class="sum last align-right">{static_data["Label"]["Incl"]} {static_data["Label"]["VAT"]}</td>
                            <td class="sum last align-right">&nbsp;</td>
                            <td class="sum last align-right">€ {dyn_data["Order"]["TotalIncl"]}</td>
                        </tr>
                    </tfoot>
                </table>
                <!-- INVOICE ITEMS END --><!-- EXTRA INFO START -->

                <table cellpadding="1" cellspacing="0" class="payment">
                    <tbody>
                        <tr>
                            <td colspan="2" style="width: 70%;">&nbsp;
                                <div><strong>{dyn_data["Order"]["Comments"]}</strong></div>
                                {dyn_data["Order"]["LegalInfo"]}

                                <div>{static_data["Label"]["SixPercentVatCertificate"]}</div>
                                <br />
                                <div>{static_data["Label"]["CnoteComment"]}</div>
                                <div>{static_data["Label"]["GeneralConditions"]}</div>
                            </td>
                        </tr>
                    </tbody>
                </table>

                <table cellpadding="1" cellspacing="0" class="contact">
                    <tbody>
                        <tr>
                            <td colspan="1" rowspan="2" style="width: 30%;">
                                <strong>{static_data["Label"]["Contact"]}</strong>

                                <div>{static_data["Me"]["Website"]}</div>
                                {static_data["Me"]["Email"]}<br />
                                {static_data["Me"]["Phone"]}
                                <div>{static_data["Me"]["Mobile"]}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 70%;">
                                <table border="0" cellpadding="1" cellspacing="1" style="text-align: right; width: 100%;">
                                    <tbody>
                                        <tr>
                                            <td style="width: 70%;"><strong>&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;"></td>
                                        </tr>
                                        <tr>
                                            <td style="width: 70%;"><strong>&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;"></td>
                                        </tr>
                                        <tr>
                                            <td style="width: 70%;"><strong>&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;"></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </body>
    </html>
    """
    filename = f"/tmp/bill_{dyn_data['id']}.pdf"
    html_to_pdf(html_content, filename)
    return filename
