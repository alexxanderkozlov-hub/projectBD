import psycopg2
import json

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
    "options": "-c client_encoding=UTF8"
}


def run_task_4(user_id, name):
    """
    4.2 Уязвимая вставка данных через f-строку (INSERT).
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Создаем временную таблицу для теста, если её нет
        cursor.execute("CREATE TABLE IF NOT EXISTS api_users (id int, name text);")

        # УЯЗВИМЫЙ ЗАПРОС
        # Если в name придет: John'); DROP TABLE api_users; --
        query = f"INSERT INTO api_users (id, name) VALUES ({user_id}, '{name}');"

        cursor.execute(query)
        conn.commit()

        return "Данные успешно добавлены (или команда выполнена)", query, "Таблица на месте"
    except Exception as e:
        return f"Ошибка: {str(e)}", "Error", "Таблица удалена или возник сбой"
    finally:
        if conn: conn.close()


def run_task_4_safe(user_id, name):
    """
    4.3 Безопасная вставка через параметры.
    """
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS api_users (id int, name text);")

        # БЕЗОПАСНЫЙ ЗАПРОС
        query = "INSERT INTO api_users (id, name) VALUES (%s, %s);"

        cursor.execute(query, (user_id, name))
        conn.commit()

        return "Данные успешно добавлены (безопасно)", query, "Таблица защищена"
    except Exception as e:
        return f"Ошибка: {str(e)}", "Error", "Ошибка"
    finally:
        if conn: conn.close()