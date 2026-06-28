import jaydebeapi

from src.database import access


if __name__ == "__main__":
    while (query := input("Enter sql query (or 'exit' to quit): ")) != "exit":
        try:
            result = access.get_connection().execute_query(query)
        except jaydebeapi.DatabaseError as e:
            print(f"Database error: {e}")
            continue
        if isinstance(result, list):
            for row in result:
                print(row)
        else:
            print(result)