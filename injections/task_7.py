import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_7(user_id):
    """
    7.1 УЯЗВИМАЯ версия: UNION-based SQL injection
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Инициализация таблицы (как у тебя)
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS task7_users
                       (
                           id
                           INT
                           PRIMARY
                           KEY,
                           name
                           VARCHAR
                       (
                           100
                       ) NOT NULL,
                           email VARCHAR
                       (
                           100
                       )
                           );
                       """)
        cursor.execute("DELETE FROM task7_users;")
        cursor.execute("""
                       INSERT INTO task7_users (id, name, email)
                       VALUES (1, 'Alice', 'alice@example.com'),
                              (2, 'Bob', 'bob@example.com');
                       """)
        conn.commit()

        # Формируем запрос (используем CAST, чтобы инъекция строк была проще)
        query = f"SELECT CAST(id AS text), name FROM task7_users WHERE id = {user_id}"

        cursor.execute(query)
        results = cursor.fetchall()
        return results, query, "УЯЗВИМО"

    except Exception as e:
        return [], str(query) if 'query' in locals() else "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()


def run_task_7_safe(user_id):
    """
    7.3 БЕЗОПАСНАЯ версия: Параметризация
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = "SELECT CAST(id AS text), name FROM task7_users WHERE id = %s"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()

        return results, query % user_id, "БЕЗОПАСНО"
    except Exception as e:
        return [], "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()