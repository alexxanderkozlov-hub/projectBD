from db.database import get_db

def get_user_by_login(login):
    """Ищет пользователя в БД и возвращает словарь с данными"""
    conn = get_db()
    cur = conn.cursor()

    # Используем %s для PostgreSQL
    cur.execute(
        "SELECT id, login, password, role FROM users WHERE login = %s",
        (login,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    # Если пользователь найден, собираем словарь
    if row:
        return {
            "id": row[0],
            "login": row[1],
            "password": row[2],
            "role": row[3]
        }

    return None

# Делаем копию функции под старым именем, чтобы app.py не выдавал ImportError
find_user_by_login = get_user_by_login