import psycopg2

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}


def run_task_10(user_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 10.1. Реализация динамического SQL (УЯЗВИМО)
    # Мы собираем строку запроса внутри блока PL/pgSQL
    query = f"""
    DO $$
    BEGIN
        EXECUTE 'SELECT * FROM logs WHERE id = {user_id}';
    END $$;
    """

    status = "Выполнение динамического SQL..."
    try:
        cursor.execute(query)
        conn.commit()
        status = "Динамический запрос выполнен успешно."
    except Exception as e:
        conn.rollback()
        status = f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

    return [], query, status


def run_task_10_safe(user_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 10.3. Исправление через USING
    # Параметр передается отдельно, а не склеивается со строкой
    query = """
    DO $$
    BEGIN
        EXECUTE 'SELECT * FROM logs WHERE id = $1' USING %s;
    END $$;
    """

    status = "Безопасное выполнение динамического SQL..."
    try:
        # В psycopg2 мы передаем значение для USING
        cursor.execute(query, (user_id,))
        conn.commit()
        status = "Запрос через USING выполнен успешно."
    except Exception as e:
        conn.rollback()
        status = f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

    return [], query, status