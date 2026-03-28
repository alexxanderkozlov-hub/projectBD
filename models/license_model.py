from db.database import get_db

def get_all_licenses():
    """Получает список лицензий с названиями продуктов через JOIN"""
    conn = get_db()
    cur = conn.cursor()
    # Используем INNER JOIN, чтобы соединить лицензию с продуктом
    query = """
        SELECT l.license_id, p.name, l.license_type, l.duration_days 
        FROM licenses l
        JOIN products p ON l.product_id = p.product_id
        ORDER BY l.license_id
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_license(product_id, license_type, duration_days):
    """Добавляет новую лицензию"""
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
    """Находит одну лицензию для редактирования"""
    conn = get_db()
    cur = conn.cursor()
    # Нам нужен product_id для выпадающего списка в форме
    cur.execute("SELECT license_id, product_id, license_type, duration_days FROM licenses WHERE license_id = %s", (lic_id,))
    lic = cur.fetchone()
    cur.close()
    conn.close()
    return lic

def update_license(lic_id, product_id, lic_type, duration):
    """Обновляет данные лицензии"""
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
    """Удаляет лицензию"""
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