from db.database import get_db


def get_user_by_login(login):
    """
    Ищет пользователя в БД по логину (без учета регистра).
    Возвращает словарь с данными для авторизации.
    """
    conn = get_db()
    if not conn:
        print("[ОШИБКА БД] Не удалось установить соединение с базой данных.")
        return None

    cur = conn.cursor()

    try:
        # Приводим и логин в базе, и вводимый логин к нижнему регистру (LOWER)
        # Это исключит ошибки, если в базе 'user', а ты ввел 'User'
        cur.execute("""
                    SELECT u.user_id, u.login, u.password_hash, r.role_name
                    FROM users u
                             JOIN roles r ON u.role_id = r.role_id
                    WHERE LOWER(u.login) = LOWER(%s)
                    """, (login.strip(),))

        row = cur.fetchone()

        if row:
            user_dict = {
                "id": row[0],  # user_id
                "login": row[1],  # оригинальный login из базы
                "password": row[2],  # password_hash (bcrypt)
                "role": row[3]  # 'Администратор' или 'Покупатель'
            }
            print(f"[БД] Пользователь '{login}' найден. Роль: {user_dict['role']}")
            return user_dict

        print(f"[БД] Пользователь '{login}' НЕ найден в таблице users.")
        return None

    except Exception as e:
        print(f"[ОШИБКА БД] Критическая ошибка при поиске: {e}")
        return None
    finally:
        cur.close()
        conn.close()


# Копия для совместимости с app.py и другими роутами
find_user_by_login = get_user_by_login