import psycopg2
import time

# Используем твои настройки подключения
DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}


def run_task_9(name_val):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # УЯЗВИМО: Вставка через f-строку
    # Мы позволяем пользователю вставить что угодно в имя
    query = f"SELECT login FROM users WHERE login = '{name_val}';"

    start_time = time.time()
    status = "Поиск завершен"
    results = []

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.commit()
    except Exception as e:
        conn.rollback()
        status = f"Ошибка: {e}"

    end_time = time.time()
    duration = round(end_time - start_time, 2)
    status += f" (Время ответа сервера: {duration} сек.)"

    cursor.close()
    conn.close()
    return results, query, status


def run_task_9_safe(name_val):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # БЕЗОПАСНО: Параметризация через %s
    query = "SELECT login FROM users WHERE login = %s;"

    start_time = time.time()
    try:
        cursor.execute(query, (name_val,))
        results = cursor.fetchall()
        conn.commit()
        status = "Поиск выполнен безопасно"
    except Exception as e:
        conn.rollback()
        results, status = [], f"Ошибка: {e}"

    end_time = time.time()
    duration = round(end_time - start_time, 2)
    status += f" (Время ответа сервера: {duration} сек.)"

    cursor.close()
    conn.close()
    return results, query, status