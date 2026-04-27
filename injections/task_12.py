import psycopg2

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


# =========================
# УЯЗВИМЫЙ РЕЖИМ
# =========================
def run_task_12(sort_param: str):
    """
    УЯЗВИМЫЙ режим: прямая вставка ORDER BY (для лабораторной)
    """
    conn = None
    status = "Список лицензий отсортирован"
    results = []

    # ⚠️ ВАЖНО: используем РЕАЛЬНЫЕ колонки из БД
    query_text = f"""
        SELECT license_id, license_type, duration_days
        FROM licenses
        ORDER BY {sort_param};
    """

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query_text)

        if cur.description:
            results = cur.fetchall()

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        status = f"Ошибка БД: {str(e)}"

    finally:
        if conn:
            conn.close()

    return results, query_text, status


# =========================
# БЕЗОПАСНЫЙ РЕЖИМ (С ЖЕСТКОЙ ОШИБКОЙ)
# =========================
def run_task_12_safe(sort_param: str):
    """
    Безопасный режим: allowlist сортировки с блокировкой при неверном вводе
    """
    conn = None
    status = "Список лицензий отсортирован (безопасно)"
    results = []
    query_text = "Запрос не был сформирован из-за ошибки безопасности."

    ALLOWED_COLUMNS = {
        "id": "license_id",
        "type": "license_type",
        "duration": "duration_days"
    }

    clean_val = sort_param.lower().strip()

    try:
        # ПРОВЕРКА: Если ввода нет в списке разрешенных, вызываем ошибку
        if clean_val not in ALLOWED_COLUMNS:
            raise ValueError(f"Недопустимый параметр сортировки: '{sort_param}'")

        safe_column = ALLOWED_COLUMNS[clean_val]

        query_text = f"""
            SELECT license_id, license_type, duration_days
            FROM licenses
            ORDER BY {safe_column};
        """

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query_text)
        results = cur.fetchall()

    except ValueError as ve:
        # Обработка нашей ошибки валидации
        status = f"Ошибка безопасности: {str(ve)}"
        results = []  # Очищаем результаты, чтобы таблица была пустой
    except Exception as e:
        # Обработка системных ошибок БД
        status = f"Ошибка БД: {str(e)}"
        results = []
    finally:
        if conn:
            conn.close()

    return results, query_text, status