import database.access as access


def get_customers(fields: list, filters: dict = None) -> list:
    fields = [f'`{field}`' for field in fields]
    query = f'SELECT {", ".join(fields)} FROM Client'
    if filters:
        filter_clauses = [f"{key} = ?" for key in filters.keys()]
        query += ' WHERE ' + ' AND '.join(filter_clauses)

    results = access.get_connection().execute_query(query, tuple(filters.values()) if filters else ())

    return results


def create_customer(data: dict) -> int:
    fields = [f'`{field}`' for field in data.keys()]
    fields = ', '.join(fields)
    placeholders = ', '.join(['?'] * len(data))
    query = f'INSERT INTO Client ({fields}) VALUES ({placeholders})'

    values = [data[key] if data[key] != '' else None for key in data.keys()]
    access.get_connection().execute_query(query, tuple(values))

    return get_last_customer_id()


def update_customer(customer_id: int, data: dict) -> None:
    set_clauses = ', '.join([f"`{key}` = ?" for key in data.keys()])
    query = f'UPDATE Client SET {set_clauses} WHERE Numero = ?'

    values = [data[key] if data[key] != '' else None for key in data.keys()]
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
