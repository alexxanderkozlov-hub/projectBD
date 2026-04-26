import psycopg2  # Вместо sqlite3
from psycopg2 import sql

# Настройки подключения (заполни своими данными из pgAdmin)
DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}


def init_db():
    # Подключаемся к PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    # Синтаксис PostgreSQL немного отличается (например, SERIAL вместо AUTOINCREMENT)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS logs
                   (
                       id
                       SERIAL
                       PRIMARY
                       KEY,
                       user_agent
                       TEXT,
                       timestamp
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    conn.commit()
    cursor.close()
    conn.close()


# Инициализация таблицы
init_db()


def run_task_8(ua_string):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # УЯЗВИМО: Прямая вставка строки через f-строку
    query = f"INSERT INTO logs (user_agent) VALUES ('{ua_string}');"
    status = "Попытка записи заголовка..."

    try:
        # В psycopg2 для выполнения нескольких команд (инъекции)
        # используется тот же execute
        cursor.execute(query)
        conn.commit()
        status = "Данные успешно записаны в таблицу logs (Уязвимо)."
    except Exception as e:
        conn.rollback()  # Откатываем транзакцию при ошибке
        status = f"Ошибка выполнения: {e}"
    finally:
        cursor.close()
        conn.close()

    return [], query, status


def run_task_8_safe(ua_string):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # БЕЗОПАСНО: Используем %s как плейсхолдер для PostgreSQL
    query = "INSERT INTO logs (user_agent) VALUES (%s);"
    status = ""

    try:
        cursor.execute(query, (ua_string,))
        conn.commit()
        status = "Заголовок безопасно сохранен в logs."
    except Exception as e:
        conn.rollback()
        status = f"Ошибка: {e}"
    finally:
        cursor.close()
        conn.close()

    return [], query, status