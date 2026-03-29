from db.database import get_db

def get_all_licenses():
    """
    Получает список лицензий с названиями продуктов через JOIN.
    ВАЖНО: Порядок колонок в SELECT соответствует ожиданиям в dashboard_routes.
    """
    conn = get_db()
    cur = conn.cursor()
    # Соединяем лицензии (l) и продукты (p)
    # Порядок: Название продукта, Тип лицензии, Дни, ID лицензии
    query = """
        SELECT p.name, l.license_type, l.duration_days, l.license_id 
        FROM licenses l
        JOIN products p ON l.product_id = p.product_id
        ORDER BY l.license_id
    """
    try:
        cur.execute(query)
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Ошибка получения списка лицензий: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def add_license(product_id, license_type, duration_days):
    """Добавляет новую лицензию в БД"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO licenses (product_id, license_type, duration_days) VALUES (%s, %s, %s)",
            (product_id, license_type, duration_days)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка добавления лицензии: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_license_by_id(lic_id):
    """Находит одну лицензию по ID"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT license_id, product_id, license_type, duration_days FROM licenses WHERE license_id = %s",
            (lic_id,)
        )
        lic = cur.fetchone()
        return lic
    except Exception as e:
        print(f"Ошибка поиска лицензии: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def update_license(lic_id, product_id, lic_type, duration):
    """Обновляет данные существующей лицензии"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE licenses SET product_id = %s, license_type = %s, duration_days = %s WHERE license_id = %s",
            (product_id, lic_type, duration, lic_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка UPDATE лицензии: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def delete_license_by_id(lic_id):
    """Удаляет лицензию по ID"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM licenses WHERE license_id = %s", (lic_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка DELETE лицензии: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_licenses_with_products():
    """
    Дублирующая функция для явного вызова JOIN-данных,
    если в dashboard_routes используется именно это имя.
    """
    return get_all_licenses()