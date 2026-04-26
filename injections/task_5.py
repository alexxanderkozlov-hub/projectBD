import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_5(user_id):
    """
    5.2 Уязвимый запрос с использованием CTE.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Создаем таблицу для теста, если её нет
        cursor.execute("DELETE FROM cte_test;")
        cursor.execute("""
                       INSERT INTO cte_test (id, info)
                       VALUES (1, 'Alice'),
                              (2, 'Bob'),
                              (3, 'Charlie') ON CONFLICT DO NOTHING;
                       """)

        # УЯЗВИМЫЙ ЗАПРОС (f-строка внутри WITH)
        # Если придет: 1; DROP TABLE cte_test; --
        query = f"""
        WITH user_data AS (
            SELECT * FROM cte_test WHERE id = {user_id}
        )
        SELECT * FROM user_data;
        """

        cursor.execute(query)
        # Пытаемся получить данные (если таблица удалится, тут может быть ошибка)
        results = cursor.fetchall() if cursor.description else []
        conn.commit()

        return results, query, "Таблица на месте"
    except Exception as e:
        return [], "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()


def run_task_5_safe(user_id):
    """
    5.3 Безопасный запрос с CTE и параметрами.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS cte_test (id int, info text);")

        # БЕЗОПАСНЫЙ ЗАПРОС (%s)
        query = """
                WITH user_data AS (SELECT * \
                                   FROM cte_test \
                                   WHERE id = %s)
                SELECT * \
                FROM user_data; \
                """

        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        conn.commit()

        return results, query, "Таблица защищена параметризацией"
    except Exception as e:
        return [], "Error", f"Ошибка: {str(e)}"
    finally:
        if conn: conn.close()