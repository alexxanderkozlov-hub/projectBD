from db.database import get_db


# =========================
# GET ALL LICENSES (ADMIN)
# =========================
def get_all_licenses():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                l.license_id,
                p.name,
                l.license_type,
                l.duration_days
            FROM licenses l
            JOIN products p ON l.product_id = p.product_id
        """)

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


# =========================
# GET LICENSES (SHOP / USER)
# =========================
def get_licenses_with_products():
    """Получает список всех лицензий с привязанными к ним продуктами,
    отсортированный по возрастанию ID"""
    conn = get_db()
    cur = conn.cursor()

    try:
        # Добавлена сортировка ORDER BY по ID лицензии (ASC - по возрастанию)
        cur.execute("""
            SELECT 
                l.license_id,
                p.name,
                l.license_type,
                l.duration_days,
                p.price
            FROM licenses l
            JOIN products p ON l.product_id = p.product_id
            ORDER BY l.license_id ASC
        """)

        return cur.fetchall()

    except Exception as e:
        print(f"Ошибка получения лицензий: {e}")
        return []

    finally:
        cur.close()
        conn.close()


# =========================
# ADD LICENSE
# =========================
def add_license(product_id, license_type, duration_days):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO licenses (product_id, license_type, duration_days)
            VALUES (%s, %s, %s)
        """, (product_id, license_type, duration_days))

        conn.commit()
        return True

    except Exception as e:
        print(f"Ошибка добавления лицензии: {e}")
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


# =========================
# GET LICENSE BY ID
# =========================
def get_license_by_id(lic_id):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT license_id, product_id, license_type, duration_days
            FROM licenses
            WHERE license_id = %s
        """, (lic_id,))

        return cur.fetchone()

    except Exception as e:
        print(f"Ошибка поиска лицензии: {e}")
        return None

    finally:
        cur.close()
        conn.close()


# =========================
# UPDATE LICENSE
# =========================
def update_license(lic_id, product_id, lic_type, duration):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            UPDATE licenses
            SET product_id = %s,
                license_type = %s,
                duration_days = %s
            WHERE license_id = %s
        """, (product_id, lic_type, duration, lic_id))

        conn.commit()
        return True

    except Exception as e:
        print(f"Ошибка UPDATE лицензии: {e}")
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


# =========================
# DELETE LICENSE
# =========================
def delete_license_by_id(lic_id):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            DELETE FROM licenses
            WHERE license_id = %s
        """, (lic_id,))

        conn.commit()
        return True

    except Exception as e:
        print(f"Ошибка DELETE лицензии: {e}")
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()