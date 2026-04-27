import psycopg2
import time

DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}


# =========================
# УЯЗВИМАЯ ВЕРСИЯ
# =========================
def run_task_9(name_val):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # УЯЗВИМО (строковая вставка)
    query = f"SELECT login FROM users WHERE login = '{name_val}';"

    start_time = time.time()
    results = []
    status = "Поиск завершен"

    try:
        cursor.execute(query)
        results = cursor.fetchall()

    except Exception as e:
        results = []
        status = f"Ошибка: {e}"

    end_time = time.time()

    duration = end_time - start_time
    status += f" (Время ответа сервера: {round(duration, 2)} сек.)"

    cursor.close()
    conn.close()

    return results, query, status


# =========================
# БЕЗОПАСНАЯ ВЕРСИЯ
# =========================
def run_task_9_safe(name_val):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = "SELECT login FROM users WHERE login = %s;"

    start_time = time.time()

    try:
        cursor.execute(query, (name_val,))
        results = cursor.fetchall()
        status = "Поиск выполнен безопасно"

    except Exception as e:
        results = []
        status = f"Ошибка: {e}"

    end_time = time.time()

    duration = end_time - start_time
    status += f" (Время ответа сервера: {round(duration, 2)} сек.)"

    cursor.close()
    conn.close()

    return results, query, status