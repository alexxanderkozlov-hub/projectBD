import random
from db.database import get_db

def generate_key_code():
    """Генерирует ключ формата XXXX-XXXX-XXXX-XXXX-XXXX"""
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    parts = [''.join(random.choices(chars, k=4)) for _ in range(5)]
    return '-'.join(parts)

def make_purchase(user_id, license_id):
    """Оформляет покупку и генерирует ключ в одной транзакции"""
    conn = get_db()
    if not conn:
        return False

    cur = conn.cursor()
    try:
        # 1. Фиксируем покупку (только ID юзера и ID лицензии)
        cur.execute(
            "INSERT INTO purchases (user_id, license_id) VALUES (%s, %s) RETURNING purchase_id",
            (user_id, license_id)
        )

        # 2. Генерируем ключ
        new_key_code = generate_key_code()

        # 3. Добавляем ключ в таблицу license_keys
        cur.execute(
            "INSERT INTO license_keys (license_id, license_key, status) VALUES (%s, %s, %s)",
            (license_id, new_key_code, 'Активен')
        )

        conn.commit()
        return True
    except Exception as e:
        print(f"[DB ERROR] Ошибка транзакции покупки: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_all_purchases():
    """Получает сырые данные о покупках (ID вместо имен)"""
    conn = get_db()
    if not conn:
        return []

    cur = conn.cursor()
    try:
        # Убрали JOIN. Теперь берем только колонки из таблицы purchases
        cur.execute("""
            SELECT purchase_id, user_id, license_id, purchase_date 
            FROM purchases 
            ORDER BY purchase_date DESC
        """)

        rows = cur.fetchall()

        # Собираем список словарей, используя только ID
        purchases = []
        for row in rows:
            purchases.append({
                "id": row[0],          # ID покупки
                "user_id": row[1],     # ID пользователя (например, 2)
                "license_id": row[2],  # ID лицензии (например, 1)
                "date": row[3].strftime("%Y-%m-%d %H:%M:%S") if row[3] else "Нет даты"
            })
        return purchases

    except Exception as e:
        print(f"[DB ERROR] Ошибка получения истории покупок: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def delete_purchase(purchase_id):
    """Удаляет запись о покупке по её ID"""
    conn = get_db()
    if not conn:
        return False
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM purchases WHERE purchase_id = %s", (purchase_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка при удалении покупки: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()