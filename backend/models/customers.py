from database.access import get_connection


def get_customers(fields: list, filters: dict = None) -> list:
    fields = [f'`{field}`' for field in fields]
    query = f'SELECT {", ".join(fields)} FROM Client'
    if filters:
        filter_clauses = [f"{key} = ?" for key in filters.keys()]
        query += ' WHERE ' + ' AND '.join(filter_clauses)
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, tuple(filters.values()) if filters else ())
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    return results


def create_customer(data: dict) -> int:
    fields = [f'`{field}`' for field in data.keys()]
    fields = ', '.join(fields)
    placeholders = ', '.join(['?'] * len(data))
    query = f'INSERT INTO Client ({fields}) VALUES ({placeholders})'
    connection = get_connection()
    cursor = connection.cursor()
    values = [data[key] if data[key] != '' else None for key in data.keys()]
    cursor.execute(query, tuple(values))
    connection.commit()
    cursor.close()
    connection.close()
    return get_last_customer_id()


def update_customer(customer_id: int, data: dict) -> None:
    set_clauses = ', '.join([f"`{key}` = ?" for key in data.keys()])
    query = f'UPDATE Client SET {set_clauses} WHERE Numero = ?'
    connection = get_connection()
    cursor = connection.cursor()
    values = [data[key] if data[key] != '' else None for key in data.keys()]
    cursor.execute(query, tuple(values) + (customer_id,))
    connection.commit()
    cursor.close()
    connection.close()


def delete_customer(customer_id: int) -> None:
    query = 'DELETE FROM Client WHERE Numero = ?'
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, (customer_id,))
        connection.commit()
    except Exception as e:
        if check_customer_exists(customer_id):
            raise e

    cursor.close()
    connection.close()


def get_last_customer_id() -> int:
    query = 'SELECT MAX(Numero) FROM Client'
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result and result[0] is not None else 0


def check_customer_exists(customer_id: int) -> bool:
    query = 'SELECT 1 FROM Client WHERE Numero = ?'
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(query, (customer_id,))
    exists = cursor.fetchone() is not None
    cursor.close()
    connection.close()
    return exists
