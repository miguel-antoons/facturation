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
    "FR": "Taux de TVA: En l'absence de contestation par écrit, dans un délai d'un mois à compter de la réception de la"
          " facture, le client est présumé reconnaître que (1) les travaux sont effectués dans un bâtiment dont la "
          "première occupation a eu lieu au cours d'une année civile qui précède d'au moins dix ans de la date de la "
          "première facture realtive à ces travaux, (2) qu'après l'exécution de ces travaux, l'habitation est utilisée,"
          " soit exclusivement soit à titre principal comme logement privé et (3) que ces travaux sont fournis et "
          "facturés à un consommateur final. Si au moins une de ces conditions n'est pas remplie, le taux normal de TVA "
          "de 21 p.c. sera applicable et le client endossera, par rapport à ces conditions, la responsabilité quant au "
          "paiement de la taxe, des intérêts et des amendes dus.",
}

static_nl = {
    "Label": {
        "AboutInvoiceNumber": "Betreft factuurnummer",
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
        "CnoteComment": "BTW terug te storten aan de staat in de mate waarin ze oorspronkelijk in aftrek werd gebracht.",
    },
    "Me": me
}

static_fr = {
    "Label": {
        "AboutInvoiceNumber": "Numéro de facture de l'objet",
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
        "CnoteComment": "Rembourser la TVA à l'état dans la mesure où elle a été initialement déduite.",
    },
    "Me": me
}

def cnote_static_fr():
    static = static_fr.copy()
    static["Label"]["OrderType"] = "Note de crédit"
    static["Label"]["OrderNumber"] = "Numéro de note de crédit"
    return static


def cnote_static_nl():
    static = static_nl.copy()
    static["Label"]["OrderType"] = "Creditnota"
    static["Label"]["OrderNumber"] = "Creditnota nummer"
    return static


def bill_static_fr():
    static = static_fr.copy()
    static["Label"]["OrderType"] = "Facture"
    static["Label"]["OrderNumber"] = "Numéro de facture"
    return static


def bill_static_nl():
    static = static_nl.copy()
    static["Label"]["OrderType"] = "Factuur"
    static["Label"]["OrderNumber"] = "Factuurnummer"
    return static