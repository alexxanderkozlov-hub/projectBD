import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_2(user_input_name):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()

        # Создаем жертву
        cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id serial, info text);")
        cursor.execute("INSERT INTO test_table (info) VALUES ('Секретные данные');")

        # Уязвимый поиск
        vuln_query = f"SELECT login FROM users WHERE login LIKE '%{user_input_name}%'"
        cursor.execute(vuln_query)
        results = cursor.fetchall()

        # Проверяем, удалена ли таблица
        cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'test_table'")
        exists = cursor.fetchone()[0] > 0

        status = "Таблица 'test_table' на месте" if exists else "Таблица 'test_table' УДАЛЕНА"
        return results, status, vuln_query
    except Exception as e:
        return [], f"Ошибка: {str(e)}", "Error"
    finally:
        if conn: conn.close()


def run_task_2_safe(user_input_name):
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        safe_query = "SELECT login FROM users WHERE login LIKE %s"
        search_param = f"%{user_input_name}%"

        cursor.execute(safe_query, (search_param,))
        results = cursor.fetchall()

        return results, "Защищено параметризацией", safe_query
    except Exception as e:
        return [], str(e), "Error"
    finally:
        if conn: conn.close()