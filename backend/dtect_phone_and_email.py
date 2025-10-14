from models.customers import get_customers
from controllers.customers import detect_phones, detect_emails


def main():
    customers = get_customers(fields=['Numero', 'Commentaire'])
    formatted_customers = []
    for customer in customers:
        phone_numbers = detect_phones(customer[1])
        emails = detect_emails(customer[1])
        formatted_customer = {
            'id': customer[0],
            'comment': f"{customer[1]}\n#####{" ".join(phone_numbers)}#####{" ".join(emails)}",
        }
        print(formatted_customer['comment'])
        formatted_customers.append(formatted_customer)


if __name__ == '__main__':
    main()
