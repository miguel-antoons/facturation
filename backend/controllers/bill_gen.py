from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from dateutil import parser
from PyPDF2 import PdfMerger


me = {
    "Logo": "",
    "OfficialCompanyName": "ANTOONS Luc BV/SRL",
    "StreetAndNumber": "Leuvensebaan 201/A",
    "ZipCode": "3040",
    "City": "Huldenberg",
    "CountryName": "Belgique",
    "VAT": "BE 0885.315.931",
    "Website": "www.antoons.be",
    "Email": "luc@antoons.be",
    "Phone": "",
    "Mobile": "+32475233856",
    "Iban": "BE35 7340 1927 6737",
    "BIC": "KREDBEBB"
}

comments = {
    "NL": {
        "1": "",
        "2": "",
        "4": "",
        "21": "Verlegging van heng. Bij gebrek aan schriftelijke betwisting binnen een termijn van één maand na de"
            " ontvangst van de factuur, wordt de afnemer geacht te erkennen dat hij een belastingplichtige is "
            "gehouden tot de indiening van periodieke aangiften. Als die voorwaarde niet vervuld is, is de afnemer "
            "ten aanzien van die voorwaarde aansprakelijk voor de betaling van de verschuldigde belasting, "
            "interesten en geldboeten.",
    },
    "FR": {
        "1": "",
        "2": "",
        "4": "",
        "21": "Autoliquidation. En l’absence de contestation par écrit, dans un délai d’un mois à compter de la "
            "réception de la facture, le client est présumé reconnaître qu’il est un assujetti tenu au dépôt de "
            "déclarations périodiques. Si cette condition n’est pas remplie, le client endossera, par rapport à "
            "cette condition, la responsabilité quant au paiement de la taxe, des intérêts et des amendes dus.",
    },
}

six_percent_certificate = {
    "NL": "Btw-tarief: Bij gebrek aan schriftelijke betwisting binnen een termijn van één maand vanaf de ontvangst van "
          "de factuur, wordt de klant geacht te erkennen dat (1) de werken worden verricht aan een woning waarvan de "
          "eerste ingebruikneming heeft plaatsgevonden in een kalenderjaar dat ten minste tien jaar voorafgaat aan de "
          "datum van de eerste factuur met betrekking tot die werken, (2) de woning, na uitvoering van die werken, "
          "uitsluitend of hoofdzakelijk als privé-woning wordt gebruikt en (3) de werken worden versterkt en "
          "gefactureerd aan een eindverbruiker. Wanneer minstens één van die voorwaarden niet is voldaan, zal het "
          "normale BTW-tarief van 21 pct. van toepassing zijn en is de afnemer ten aanzien van die voorwaarden "
          "aansprakelijk voor de betaling van de verschuldigde belasting, interesten en geldboeten.",
    "FR": "Certificat pour le taux de TVA réduit de 6% pour les travaux de rénovation de logements "
          "de plus de 10 ans disponible sur demande.",
}


def create_bill(req_data: dict):
    if req_data["CounterParty"]["Language"].upper() == "FR":
        return fr_bill(req_data)
    else:
        return nl_bill(req_data)


def format_dyn_data(req_data: dict):
    return {
        "id": req_data["OrderID"],
        "Order": {
            "OrderNumber": req_data["OrderNumber"],
            "OrderDate": parser.parse(req_data["OrderDate"]).strftime("%d/%m/%Y"),
            "DeliveryDate": parser.parse(req_data["DeliveryDate"]).strftime("%d/%m/%Y"),
            "ExpiryDate": parser.parse(req_data["ExpiryDate"]).strftime("%d/%m/%Y"),
            "Title": req_data["OrderTitle"],
            "YourReference": f"{req_data['OrderNumber']}",
            "VAT": '{0:.2f}'.format(req_data["OrderLines"][0]["VATPercentage"]).replace(".", ","),
            "TotalExcl": '{0:.2f}'.format(req_data["TotalExcl"]).replace(".", ","),
            "TotalVAT": '{0:.2f}'.format(req_data["TotalVAT"]).replace(".", ","),
            "TotalIncl": '{0:.2f}'.format(req_data["TotalIncl"]).replace(".", ","),
            "Comments": "",
            "LegalInfo": comments[req_data["CounterParty"]["Language"].upper()][req_data["VentilationCode"]],
            "OGM": req_data["PaymentReference"],
        },
        "Customer": {
            "OfficialCompanyName": req_data["CounterParty"].get("Name", ""),
            "ContactFullName": req_data["CounterParty"].get("Contact", ""),
            "StreetAndNumber": f"{req_data["CounterParty"]["Street"]} {req_data["CounterParty"]["StreetNumber"]} {req_data["CounterParty"].get("Box", "")}".strip(),
            "ZipCode": req_data["CounterParty"]["Addresses"][0]["Zipcode"],
            "City": req_data["CounterParty"]["Addresses"][0]["City"],
            "CountryName": "",
            "VAT": req_data["CounterParty"].get("VATNumber", ""),
            "Nr": req_data["CounterParty"]["Nr"],
        },
        "OrderLines": list(map(
            lambda line: {
                "Description": line["Description"],
                "AmountExcl": '{0:.2f}'.format(line["UnitPriceExcl"]).replace(".", ","),
                "Quantity": str(int(line["Quantity"])) if line["Quantity"].is_integer() else '{0:.2f}'.format(line["Quantity"]).replace(".", ","),
                "Unit": line.get("Unit", ""),
                "TotalExcl": '{0:.2f}'.format(line["TotalExcl"]).replace(".", ","),
                "VATPercentage": '{0:.0f}'.format(line["VATPercentage"]),
                "TotalIncl": '{0:.2f}'.format(line["TotalIncl"]).replace(".", ","),
            }, req_data["OrderLines"]
        )),
    }


def nl_bill(req_data):
    static_data = {
        "Label": {
            "OrderType": "Factuur",
            "OrderNumber": "Factuurnummer",
            "Date": "Datum",
            "DeliveryDate": "Leveringsdatum",
            "ExpiryDate": "Vervaldatum",
            "CustomerNumber": "Klantennummer",
            "Re": "Betreft",
            "YourReference": "Uw referentie",
            "Description": "OMSCHRIJVING",
            "UnitPrice": "PRIJS PER",
            "Count": "AANTAL",
            "Unit": "EENH.",
            "Excl": "EXCL.",
            "VAT": "BTW",
            "Incl": "INCL.",
            "Total": "TOTAAL",
            "GeneralConditions": "De algemende verkoopsvoorwaarden van toepassing zijn aan de keerzijde van dit blad.",
            "Contact": "Contact",
            "OGM": "OGM",
            "Iban": "IBAN",
            "BIC": "BIC",
            "SixPercentVatCertificate": six_percent_certificate["NL"] if req_data["VentilationCode"] == "2" else "",
        },
        "Me": me
    }
    dyn_data = format_dyn_data(req_data)
    return bill_gen(static_data, dyn_data)


def fr_bill(req_data):
    static_data = {
        "Label": {
            "OrderType": "Facture",
            "OrderNumber": "Numéro de facture",
            "Date": "Date",
            "DeliveryDate": "Date de livraison",
            "ExpiryDate": "Date d'échéance",
            "CustomerNumber": "N° de client",
            "Re": "Objet",
            "YourReference": "Votre référence",
            "Description": "DESCRIPTION",
            "UnitPrice": "P.U.",
            "Count": "QUANTITÉ",
            "Unit": "UNITÉ",
            "Excl": "EXCL.",
            "VAT": "TVA",
            "Incl": "INCL.",
            "Total": "TOTAL",
            "GeneralConditions": "Les conditions générales de vente en vigueur se trouvent au verso de cette feuille.",
            "Contact": "Contact",
            "OGM": "OGM",
            "Iban": "IBAN",
            "BIC": "BIC",
            "SixPercentVatCertificate": six_percent_certificate["FR"] if req_data["VentilationCode"] == "2" else "",
        },
        "Me": me
    }
    dyn_data = format_dyn_data(req_data)
    return bill_gen(static_data, dyn_data)


def html_to_pdf(html_content, output_path):
    font_config = FontConfiguration()
    css = CSS("./pdf/pdf.css", font_config=font_config)
    HTML(string=html_content).write_pdf("/tmp/temp_bill.pdf", stylesheets=[css], font_config=font_config)

    merger = PdfMerger()
    merger.append("/tmp/temp_bill.pdf")
    merger.append("./pdf/verkoopsvoorwaarden.pdf")
    with open(output_path, "wb") as pdf_file:
        merger.write(pdf_file)
    merger.close()


def bill_gen(static_data, dyn_data):
    unit_is_empty = all(line['Unit'] == "" for line in dyn_data['OrderLines'])

    order_string = ""
    for line in dyn_data['OrderLines']:
        price_is_not_zero = line['AmountExcl'] != "0,00"
        line_html = f"""
        <tr>
            <td class="align-left">{line['Description'].replace("\n", "<br />").replace("/r", "")}</td>
            <td class="align-right">{"€ " + line['AmountExcl'] if price_is_not_zero else ""}</td>
            <td class="align-right">{line['Quantity']}</td>
            {"" if unit_is_empty else f"<td class =\"align-left\">{line['Unit']}</td>"}
            <td class="align-right">{"€ " + line['TotalExcl'] if price_is_not_zero else ""}</td>
            <td class="align-right">{line['VATPercentage'] + " %" if price_is_not_zero else ""}</td>
            <td class="align-right">{"€ " + line['TotalIncl'] if price_is_not_zero else ""}</td>
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
                      <b>{static_data["Label"]["OrderNumber"]}:</b> {dyn_data["Order"]["OrderNumber"]}</td>
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
                            {static_data["Label"]["DeliveryDate"]}:<br />
                            {static_data["Label"]["ExpiryDate"]}: </b>
                        </td>
                        <td style="width: 30%;">
                            {dyn_data["Order"]["OrderDate"]}<br />
                            {dyn_data["Order"]["DeliveryDate"]}<br />
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
                            <td colspan="1" style="width: 70%;">&nbsp;
                                <div><strong>{dyn_data["Order"]["Comments"]}</strong></div>
                                {dyn_data["Order"]["LegalInfo"]}

                                <div>{static_data["Label"]["SixPercentVatCertificate"]}</div>

                                <div>{static_data["Label"]["GeneralConditions"]}</div>
                            </td>
                            <td colspan="1" rowspan="2" style="width: 30%;">
                                <div class="qr">&nbsp;</div>
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
                                            <td style="width: 70%;"><strong>{static_data["Label"]["OGM"]}:&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;"><span style="background-color:#ffff00;">{dyn_data["Order"]["OGM"]}</span></td>
                                        </tr>
                                        <tr>
                                            <td style="width: 70%;"><strong>{static_data["Label"]["Iban"]}:&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;">{static_data["Me"]["Iban"]}</td>
                                        </tr>
                                        <tr>
                                            <td style="width: 70%;"><strong>{static_data["Label"]["BIC"]}:&nbsp;</strong></td>
                                            <td style="width: 30%; vertical-align: bottom;">{static_data["Me"]["BIC"]}</td>
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
