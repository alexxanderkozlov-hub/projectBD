from db.database import get_db


def get_all_products():
    """Получает все продукты из базы данных PostgreSQL"""
    conn = get_db()
    cur = conn.cursor()

    try:
        # Порядок согласно твоей таблице:
        # p[0] - product_id, p[1] - name, p[2] - version, p[3] - price
        cur.execute("SELECT product_id, name, version, price FROM products ORDER BY product_id")
        rows = cur.fetchall()
    except Exception as e:
        print(f"Ошибка при выполнении SELECT: {e}")
        rows = []
    finally:
        cur.close()
        conn.close()

    return rows


def delete_product_by_id(product_id):
    """Удаляет продукт из БД по его ID"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Используем %s для безопасной передачи ID (защита от SQL-инъекций)
        cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))

        # Фиксируем изменения в базе данных (БЕЗ ЭТОГО НЕ УДАЛИТСЯ!)
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при удалении товара {product_id}: {e}")
        conn.rollback()  # Откатываем изменения, если произошла ошибка
        return False
    finally:
        cur.close()
        conn.close()

def get_product_by_id(product_id):
    """Находит один товар для редактирования"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT product_id, name, version, price FROM products WHERE product_id = %s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()
    return product

def update_product(product_id, name, version, price):
    """Обновляет данные в БД"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE products SET name = %s, version = %s, price = %s WHERE product_id = %s",
            (name, version, price, product_id)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка обновления: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def add_product(name, version, price):
    """Добавляет новый продукт в БД"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Не указываем product_id, база сама его назначит
        cur.execute(
            "INSERT INTO products (name, version, price) VALUES (%s, %s, %s)",
            (name, version, price)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при добавлении: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()