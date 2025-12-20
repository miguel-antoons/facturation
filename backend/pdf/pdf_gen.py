from dateutil import parser
from pdf.static_data import comments
import models.customers as mcust


def format_dyn_data(req_data: dict):
    return {
        "id": req_data["OrderID"],
        "Order": {
            "OrderNumber": req_data["OrderNumber"],
            "AboutInvoiceNumber": req_data.get("AboutInvoiceNumber", ""),
            "OrderDate": parser.parse(req_data["OrderDate"]).strftime("%d/%m/%Y"),
            "DeliveryDate": parser.parse(req_data.get("DeliveryDate", "12/12/2012")).strftime("%d/%m/%Y"),
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
            "Salutation": mcust.get_customers(["Titre"], filters={"Numero": req_data["CounterParty"]["Nr"]})[0][0],
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