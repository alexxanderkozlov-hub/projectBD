from models.user_model import get_user_by_login
import uuid
import bcrypt
import random  # Добавляем для генерации кода


def login(handler, data):
    login_val = data.get("login", [""])[0].strip()
    password_val = data.get("password", [""])[0].strip()

    print(f"\n[AUTH] Проверка пользователя: {login_val}")

    user = get_user_by_login(login_val)

    if not user:
        print(f"[AUTH] ОШИБКА: Пользователь '{login_val}' не найден!")
        handler.redirect("/")
        return

    # Универсальный поиск хэша
    db_password_hash = user.get("password") if isinstance(user, dict) else user[2]

    try:
        is_correct = bcrypt.checkpw(password_val.encode('utf-8'), db_password_hash.encode('utf-8'))
    except Exception as e:
        print(f"[AUTH] Ошибка bcrypt: {e}")
        is_correct = False

    if is_correct:
        session_id = str(uuid.uuid4())

        # --- ГЕНЕРАЦИЯ КОДА 2FA ---
        verification_code = str(random.randint(100000, 999999))

        # Сохраняем код в глобальный словарь codes, чтобы verify мог его проверить
        handler.__class__.codes[session_id] = verification_code

        handler.__class__.sessions[session_id] = {
            "user": user,
            "2fa": False
        }

        # ВЫВОДИМ КОД В ТЕРМИНАЛ
        print("\n" + "=" * 30)
        print(f"  ВАШ КОД 2FA: {verification_code}")
        print("=" * 30 + "\n")

        handler.send_response(302)
        handler.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly")
        handler.send_header("Location", "/2fa")
        handler.end_headers()
    else:
        print("[AUTH] ОШИБКА: Пароль не подошел.")
        handler.redirect("/")


def verify(handler, data):
    # 1. Достаем session_id из кук
    cookie_header = handler.headers.get("Cookie", "")
    session_id = None
    if "session_id=" in cookie_header:
        session_id = cookie_header.split("session_id=")[1].split(";")[0].strip()

    # 2. Достаем введенный пользователем код из формы
    # В шаблоне 2fa.html поле должно называться name="code"
    input_code = data.get("code", [""])[0].strip()

    if session_id and session_id in handler.__class__.sessions:
        # Достаем правильный код, который мы напечатали в терминале
        correct_code = handler.__class__.codes.get(session_id)

        print(f"[2FA] Проверка: введено '{input_code}', ожидалось '{correct_code}'")

        if input_code == correct_code:
            handler.__class__.sessions[session_id]["2fa"] = True
            print("[2FA] УСПЕХ! Переходим в дашборд.")
            handler.redirect("/dashboard")
            return
        else:
            print("[2FA] ОШИБКА: Неверный код.")
            handler.redirect("/2fa")  # Возвращаем на ввод кода
    else:
        print("[2FA] Ошибка сессии.")
        handler.redirect("/")