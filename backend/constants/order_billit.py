from typing import TypedDict

from constants.all import ResponseMessage, RESPONSE_ERROR, COUNTRY_CODE_BE
from constants.customer import CustomerBack
from constants.order_back import OrderBack
from controllers import customers as cctrl
from models import customers as mcust

PARTY_TYPE_CUSTOMER = "Customer"
ADDRESS_TYPE_INVOICE_ADDRESS = "InvoiceAddress"
ORDER_TYPE_INVOICE = "Invoice"
ORDER_TYPE_CREDIT_NOTE = "CreditNote"
ORDER_DIRECTION_INCOME = "Income"



# * ------------------------------------------
# * ORDER DATA STRUCTURES FOR BILLIT API
# * ------------------------------------------
class CustomerBillitAddress(TypedDict):
    AddressType: str
    Street: str
    StreetNumber: str
    Zipcode: str
    City: str
    CountryCode: str


class CustomerBillit(TypedDict):
    Nr: int
    Name: str
    VATNumber: str
    Zipcode: str
    City: str
    Street: str
    StreetNumber: str
    CountryCode: str
    ContactFirstName: str
    ContactLastName: str
    Language: str
    Email: str
    Phone: str
    Mobile: str
    PartyType: str
    Addresses: list[CustomerBillitAddress]


class BillitPDF(TypedDict):
    FileName: str
    FileContent: str


class OrderBillit(OrderBack):
    Customer: CustomerBillit
    OrderType: str
    OrderDirection: str
    OrderPDF: BillitPDF


# * ------------------------------------------
# * CONVERSION FUNCTIONS
# * ------------------------------------------
def order_from_back(order_back: OrderBack, customer_back: CustomerBack) -> OrderBillit:
    res = OrderBillit(
        Customer=customer_from_back(customer_back),
        OrderType=ORDER_TYPE_INVOICE,
        OrderDirection=ORDER_DIRECTION_INCOME,
        OrderNumber=order_back["OrderNumber"],
        OrderDate=order_back["OrderDate"],
        ExpiryDate=order_back["ExpiryDate"],
        DeliveryDate=order_back["DeliveryDate"],
        OrderTitle=order_back["OrderTitle"],
        OrderLines=order_back.get("OrderLines", []),
        VentilationCode=order_back["VentilationCode"],
    )

    if "OrderID" in order_back:
        res["OrderID"] = order_back["OrderID"]

    return res

def customer_from_back(customer: CustomerBack) -> CustomerBillit | ResponseMessage:
    if len(customer["Adresse"].split(',')) <= 1:
        print("Invalid address format for customer ID:", customer["Numero"])
        return ResponseMessage(
            status=RESPONSE_ERROR,
            message="Format d'adresse incorrect. L'adresse devrait avoir le format 'Rue , Numéro'."
        )

    customer_emails = cctrl.detect_emails(customer["Commentaire"])
    phones = cctrl.detect_phones(customer["Commentaire"])
    mobiles = cctrl.detect_mobiles(customer["Commentaire"])
    return CustomerBillit(
        Nr=customer["Numero"],
        Name=customer["Societe"],
        VATNumber=customer["TVA"],
        Zipcode=customer["Codepostal"],
        City=customer["Localite"],
        Street=mcust.get_customer_street(customer["Adresse"]),
        StreetNumber=mcust.get_customer_street_number(customer["Adresse"]),
        CountryCode=COUNTRY_CODE_BE,
        ContactFirstName=customer["Prenom"],
        ContactLastName=customer["Nom"],
        Language=customer["Langue"].upper(),
        Email=customer_emails[0] if len(customer_emails) > 0 else "",
        Phone=phones[0] if len(phones) > 0 else "",
        Mobile=mobiles[0] if len(mobiles) > 0 else "",
        PartyType=PARTY_TYPE_CUSTOMER,
        Addresses=[
            CustomerBillitAddress(
                AddressType=ADDRESS_TYPE_INVOICE_ADDRESS,
                Street=mcust.get_customer_street(customer["Adresse"]),
                StreetNumber=mcust.get_customer_street_number(customer["Adresse"]),
                City=customer["Localite"],
                Zipcode=customer["Codepostal"],
                CountryCode=COUNTRY_CODE_BE
            )
        ],
    )
