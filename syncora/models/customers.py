import database.access as access
from constants.customer_back import *


def get_customers(fields: list, filters: dict = None) -> list[CustomerBack]:
    formatted_fields = [f'`{field}`' for field in fields]
    query = f'SELECT {", ".join(formatted_fields)} FROM Client'
    if filters:
        filter_clauses = [f"{key} = ?" for key in filters.keys()]
        query += ' WHERE ' + ' AND '.join(filter_clauses)

    results = access.get_connection().execute_query(query, tuple(filters.values()) if filters else ())

    customers = []
    for customer in results:
        customers.append(CustomerBack.from_customer_db(fields, customer))

    return customers


def get_customers_dict(fields: list, filters: dict = None) -> dict[int, CustomerBack]:
    fields = [CUSTOMER_DB_ID] + fields if CUSTOMER_DB_ID not in fields else fields
    customers = get_customers(fields, filters)
    if not customers:
        return {}

    customer_dict = {}
    for customer in customers:
        customer_dict[customer.id] = customer

    return customer_dict


def create_customer(data: CustomerBack) -> int:
    fields, values = data.to_customer_db()
    fields = ', '.join(fields)
    placeholders = ', '.join(['?'] * len(values))
    query = f'INSERT INTO Client ({fields}) VALUES ({placeholders})'

    access.get_connection().execute_query(query, tuple(values))

    return get_last_customer_id()


def update_customer(customer_id: int, data: CustomerBack) -> None:
    fields, values = data.to_customer_db()
    set_clauses = ', '.join([f"`{field}` = ?" for field in fields])
    query = f'UPDATE Client SET {set_clauses} WHERE Numero = ?'

    access.get_connection().execute_query(query, tuple(values) + (customer_id,))


def delete_customer(customer_id: int) -> None:
    query = 'DELETE FROM Client WHERE Numero = ?'

    try:
        access.get_connection().execute_query(query, (customer_id,))
    except Exception as e:
        # Ignore the exception if the customer does not exist anymore
        # The reason for this is that sometimes there are errors due to foreign key constraints and the UCanAccess driver
        if check_customer_exists(customer_id):
            raise e


def get_last_customer_id() -> int:
    query = 'SELECT MAX(Numero) FROM Client'

    result = access.get_connection().execute_query(query, fetch_one=True)

    return result[0] if result and result[0] is not None else 0


def check_customer_exists(customer_id: int) -> bool:
    query = 'SELECT 1 FROM Client WHERE Numero = ?'

    result = access.get_connection().execute_query(query, (customer_id,), fetch_one=True)

    return result is not None and len(result) > 0


def get_customer_street(address: str) -> str:
    parts = address.split(',')
    return parts[0].strip() if len(parts) > 0 else ''


def get_customer_street_number(address: str) -> str:
    parts = address.split(',')
    return ''.join(parts[1:]).strip() if len(parts) > 1 else ''
