from db.database import get_db

def get_all_keys():
    """Получает список ключей, объединяя с лицензиями и продуктами"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT k.key_id, p.name, l.license_type, k.license_key, k.status
        FROM license_keys k
        JOIN licenses l ON k.license_id = l.license_id
        JOIN products p ON l.product_id = p.product_id
        ORDER BY k.key_id ASC
    """)
    keys = cur.fetchall()
    cur.close()
    conn.close()
    return keys

def add_new_key(license_id, key_code):
    """Добавляет новый ключ со статусом 'Активен'"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO license_keys (license_id, license_key, status) VALUES (%s, %s, 'Активен')",
            (license_id, key_code)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при создании ключа: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def update_key_status(key_id, new_status):
    """Меняет статус ключа (Активен, Истек, Заблокирован)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE license_keys SET status = %s WHERE key_id = %s",
            (new_status, key_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Ошибка смены статуса: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def delete_key_by_id(key_id):
    """Удаляет ключ из базы данных по его ID (ДОБАВЛЕНО)"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "DELETE FROM license_keys WHERE key_id = %s",
            (key_id,)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при удалении ключа: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()