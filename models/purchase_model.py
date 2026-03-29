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
    cur = conn.cursor()
    try:
        # 1. Фиксируем покупку в таблице purchases
        # Используем твой столбец user_id
        cur.execute(
            "INSERT INTO purchases (user_id) VALUES (%s)",
            (user_id,)
        )

        # 2. Генерируем новый код ключа
        new_key_code = generate_key_code()

        # 3. Добавляем ключ в таблицу license_keys
        # ВАЖНО: Убедись, что в license_keys столбцы называются именно так
        cur.execute(
            "INSERT INTO license_keys (license_id, license_key, status) VALUES (%s, %s, 'Активен')",
            (license_id, new_key_code)
        )

        conn.commit()
        print(f"Успешная покупка: User {user_id} купил License {license_id}")
        return True
    except Exception as e:
        print(f"Ошибка транзакции покупки: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_all_purchases():
    """Получает список всех покупок для отображения в истории"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # ИСПРАВЛЕНО: используем purchase_id и purchase_date согласно твоему CREATE TABLE
        cur.execute("""
            SELECT purchase_id, user_id, purchase_date 
            FROM purchases 
            ORDER BY purchase_date DESC
        """)
        return cur.fetchall()
    except Exception as e:
        print(f"Ошибка получения покупок из БД: {e}")
        return []
    finally:
        cur.close()
        conn.close()