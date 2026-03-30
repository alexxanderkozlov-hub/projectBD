from db.database import get_db

def get_user_by_login(login):
    """
    ВНИМАНИЕ: Эта функция НАМЕРЕННО УЯЗВИМА для SQL-инъекций.
    Используется f-строка вместо безопасных параметров %s для демонстрации взлома.
    """
    conn = get_db()
    if not conn:
        print("[ОШИБКА БД] Не удалось установить соединение с базой данных.")
        return None

    cur = conn.cursor()

    try:
        # УЯЗВИМАЯ ЧАСТЬ: Мы убрали %s и подставили переменную прямо в строку f""
        # Это позволяет закрыть кавычку вводом admin' и дописать свой код
        query = f"""
            SELECT u.user_id, u.login, u.password_hash, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.login = '{login}'
        """

        # Печатаем итоговый запрос в консоль, чтобы ты видел результат инъекции в реальном времени
        print(f"\n[!] СЕРВЕР ВЫПОЛНЯЕТ SQL ЗАПРОС: \n{query}\n")

        cur.execute(query) # Выполняем "сырой" запрос
        row = cur.fetchone()

        if row:
            user_dict = {
                "id": row[0],
                "login": row[1],
                "password": row[2],
                "role": row[3]
            }
            print(f"[БД] Пользователь найден через запрос. Роль: {user_dict['role']}")
            return user_dict

        print(f"[БД] Пользователь '{login}' не найден.")
        return None

    except Exception as e:
        print(f"[ОШИБКА БД] SQL синтаксис нарушен инъекцией: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Копия для совместимости
find_user_by_login = get_user_by_login