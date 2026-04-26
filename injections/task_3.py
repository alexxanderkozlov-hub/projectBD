import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_3(username, password):
    """
    3.2 Уязвимая проверка авторизации через f-строку.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Тот самый уязвимый запрос из задания
        # Если ввести ' OR '1'='1 в username, запрос станет истинным
        query = f"SELECT * FROM users WHERE login = '{username}' AND password_hash = '{password}'"

        cursor.execute(query)
        results = cursor.fetchall()

        status = "ВХОД РАЗРЕШЕН (Инъекция сработала)" if results else "ДОСТУП ЗАПРЕЩЕН"
        return results, status, query
    except Exception as e:
        return [], f"Ошибка: {str(e)}", "Error"
    finally:
        if conn: conn.close()


def run_task_3_safe(username, password):
    """
    3.3 Исправленная проверка через параметры.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Безопасный запрос
        query = "SELECT * FROM users WHERE login = %s AND password_hash = %s"

        cursor.execute(query, (username, password))
        results = cursor.fetchall()

        status = "ВХОД РАЗРЕШЕН" if results else "ДОСТУП ЗАПРЕЩЕН (Защита сработала)"
        return results, status, query
    except Exception as e:
        return [], str(e), "Error"
    finally:
        if conn: conn.close()