import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_6(limit, offset):
    """
    6.1 УЯЗВИМАЯ пагинация
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Таблица + данные
        cursor.execute("CREATE TABLE IF NOT EXISTS page_test (id int, name text);")
        cursor.execute("DELETE FROM page_test;")
        cursor.execute("""
        INSERT INTO page_test (id, name) VALUES
        (1, 'Alice'),
        (2, 'Bob'),
        (3, 'Charlie'),
        (4, 'David'),
        (5, 'Eve');
        """)

        # ❌ УЯЗВИМО
        query = f"""
        SELECT * FROM page_test
        LIMIT {limit} OFFSET {offset};
        """

        cursor.execute(query)
        results = cursor.fetchall()

        return results, query, "УЯЗВИМО"
    except Exception as e:
        return [], "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()


def run_task_6_safe(limit, offset):
    """
    6.3 БЕЗОПАСНАЯ версия (валидация)
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS page_test (id int, name text);")

        # ✅ ВАЛИДАЦИЯ
        try:
            limit = int(limit)
            offset = int(offset)
        except:
            return [], "Error", "limit и offset должны быть числами"

        if limit < 1 or limit > 100:
            return [], "Error", "limit должен быть от 1 до 100"

        if offset < 0:
            return [], "Error", "offset не может быть отрицательным"

        query = """
        SELECT * FROM page_test
        LIMIT %s OFFSET %s;
        """

        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()

        return results, query, "БЕЗОПАСНО"
    except Exception as e:
        return [], "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()