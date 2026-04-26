import psycopg2

# Твои настройки подключения
DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_1(user_input_id):
    """
    1.2. УЯЗВИМЫЙ ВАРИАНТ (f-строка)
    Здесь данные напрямую склеиваются с SQL-командой.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Уязвимость: ввод пользователя становится частью логики SQL
        vuln_query = f"SELECT * FROM users WHERE user_id = {user_input_id}"

        cursor.execute(vuln_query)
        result_data = cursor.fetchall()
        return result_data, vuln_query
    except Exception as e:
        if conn: conn.rollback()
        return [("Ошибка SQL", str(e), "", "", "")], "Запрос не удался"
    finally:
        if conn: conn.close()


def run_task_1_safe(user_input_id):
    """
    1.3. БЕЗОПАСНЫЙ ВАРИАНТ (Параметризация)
    Данные передаются отдельно от SQL-шаблона.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Защита: используем плейсхолдер %s
        # Драйвер psycopg2 сам экранирует ввод и передает его как значение, а не код
        safe_query = "SELECT * FROM users WHERE user_id = %s"

        # Передаем кортеж параметров (user_input_id,) вторым аргументом
        cursor.execute(safe_query, (user_input_id,))

        result_data = cursor.fetchall()
        return result_data, safe_query + f" | Параметр: {user_input_id}"
    except Exception as e:
        if conn: conn.rollback()
        return [("Ошибка безопасности", str(e), "", "", "")], "Запрос отклонен"
    finally:
        if conn: conn.close()

    return results, log_query