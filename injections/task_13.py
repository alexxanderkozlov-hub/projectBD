import psycopg2
import re

# =========================
# КОНФИГ БД
# =========================
DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}


def get_db_connection():
    """Создаёт соединение с PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)


# ============= УЯЗВИМАЯ ВЕРСИЯ (SQL ИНЪЕКЦИЯ) =============
def run_task_13(math_expr):
    """
    УЯЗВИМО! Подставляет математическое выражение прямо в SQL запрос.

    Примеры:
    - login = "1+1"  → WHERE user_id = 1+1  (найдёт user_id=2)
    - login = "2-1"  → WHERE user_id = 2-1  (найдёт user_id=1)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔴 ОПАСНО! Прямая подстановка в SQL
    query = f"SELECT user_id, login, email, role_id FROM users WHERE user_id = {math_expr}"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        results = [[row[0], row[1], row[2], row[3]] for row in rows]
        status = f"✓ Выполнен запрос с математикой: {math_expr}"

        if not results:
            status = f"⚠ Ничего не найдено. Результат: {math_expr}"

    except psycopg2.Error as e:
        results = []
        status = f"✗ Ошибка SQL: {str(e)}"

    cursor.close()
    conn.close()
    return results, query, status


# ============= БЕЗОПАСНАЯ ВЕРСИЯ (ВОЗВРАЩАЕТ ОШИБКУ) =============
def run_task_13_safe(math_expr):
    """
    БЕЗОПАСНО! НЕ выполняет математические выражения.
    Если в выражении есть операторы (+ - * /) - возвращает ошибку.
    Работает только с чистыми числами.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    expr = math_expr.strip()

    # Проверяем, есть ли в выражении операторы
    has_operators = any(op in expr for op in ['+', '-', '*', '/'])

    # Если есть операторы или это не число - возвращаем ошибку
    if has_operators or not expr.isdigit():
        results = []
        query = "Запрос не выполнен из-за небезопасного ввода"
        status = f"❌ ОШИБКА БЕЗОПАСНОГО РЕЖИМА: Выражение '{expr}' содержит математические операторы! Разрешены только чистые числа."
        cursor.close()
        conn.close()
        return results, query, status

    # Если это чистое число - выполняем безопасный запрос
    user_id = int(expr)
    query = "SELECT user_id, login, email, role_id FROM users WHERE user_id = %s"

    try:
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        results = [[row[0], row[1], row[2], row[3]] for row in rows]

        if not results:
            status = f"⚠ Пользователь с ID={user_id} не найден"
        else:
            status = f"✓ Найден пользователь с ID={user_id}"

    except psycopg2.Error as e:
        results = []
        status = f"✗ Ошибка БД: {str(e)}"

    cursor.close()
    conn.close()
    return results, query, status