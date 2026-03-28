from db.database import get_db


def get_all_products():
    """Получает все продукты из базы данных PostgreSQL"""
    conn = get_db()
    cur = conn.cursor()

    try:
        # Исправлено: используем product_id вместо id.
        # Порядок согласно твоей таблице: product_id(0), name(1), version(2), price(3)
        cur.execute("SELECT product_id, name, version, price FROM products ORDER BY product_id")
        rows = cur.fetchall()
    except Exception as e:
        print(f"Ошибка при выполнении SELECT: {e}")
        rows = []
    finally:
        cur.close()
        conn.close()

    return rows