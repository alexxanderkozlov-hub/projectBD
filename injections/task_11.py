import psycopg2

# =========================
# КОНФИГ БД (твой)
# =========================
DB_CONFIG = {
    "dbname": "kozlov",
    "user": "postgres",
    "password": "12345678",
    "host": "localhost",
    "port": "5432",
}

# =========================
# ПОДКЛЮЧЕНИЕ К БД
# =========================
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# =========================
# ❌ УЯЗВИМО (Blind SQLi)
# =========================
def run_task_11(user_input):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # ❌ УЯЗВИМО
        query = f"""
        SELECT license_id, license_type FROM licenses
        WHERE license_id = {user_input}
        """

        cur.execute(query)
        rows = cur.fetchall()

        # логика blind-инъекции (TRUE / FALSE)
        if rows:
            status = "TRUE (условие выполнилось, данные есть)"
        else:
            status = "FALSE (условие не выполнилось, данных нет)"

        return rows, query, status

    except Exception as e:
        return [], query, f"Ошибка: {str(e)}"

    finally:
        cur.close()
        conn.close()


# =========================
# ✅ БЕЗОПАСНО (параметризация)
# =========================
def run_task_11_safe(user_input):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # ✅ безопасный запрос
        # ✅ БЕЗОПАСНО
        query = """
                SELECT license_id, license_type \
                FROM licenses
                WHERE license_id = %s \
                """

        cur.execute(query, (user_input,))
        rows = cur.fetchall()

        if rows:
            status = "Данные найдены (безопасно)"
        else:
            status = "Данных нет (безопасно)"

        return rows, query, status

    except Exception as e:
        return [], query, f"Ошибка: {str(e)}"

    finally:
        cur.close()
        conn.close()