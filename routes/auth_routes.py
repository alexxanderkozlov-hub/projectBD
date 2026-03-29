import uuid
import bcrypt
import random
from models.user_model import get_user_by_login


def login(handler, data):
    # Получаем данные из формы. strip() убирает случайные пробелы
    login_val = data.get("login", [""])[0].strip()
    password_val = data.get("password", [""])[0].strip()

    print(f"\n[AUTH] Проверка пользователя: {login_val}")

    user = get_user_by_login(login_val)

    if not user:
        print(f"[AUTH] ОШИБКА: Пользователь '{login_val}' не найден!")
        handler.redirect("/")
        return

    # Извлекаем хэш пароля (теперь всегда из словаря, так как мы обновили модель)
    db_password_hash = user.get("password")

    try:
        # Проверка пароля через bcrypt
        is_correct = bcrypt.checkpw(password_val.encode('utf-8'), db_password_hash.encode('utf-8'))
    except Exception as e:
        print(f"[AUTH] Ошибка bcrypt (проверь формат хеша в БД): {e}")
        is_correct = False

    if is_correct:
        session_id = str(uuid.uuid4())
        verification_code = str(random.randint(100000, 999999))

        # Инициализация хранилищ в классе, если они еще не созданы
        if not hasattr(handler.__class__, 'codes'):
            handler.__class__.codes = {}
        if not hasattr(handler.__class__, 'sessions'):
            handler.__class__.sessions = {}

        # Сохраняем код и данные сессии
        handler.__class__.codes[session_id] = verification_code
        handler.__class__.sessions[session_id] = {
            "user": user,
            "2fa": False
        }

        # ВЫВОДИМ КОД В ТЕРМИНАЛ
        inner_width = 34

        print("\n" + "╔" + "═" * (inner_width + 2) + "╗")
        # :<{inner_width} — выравнивает текст по левому краю и добивает пробелами до 34 символов
        print(f"║ {f'КОД ДЛЯ {login_val.upper()}: {verification_code}':<{inner_width}} ║")
        print("╚" + "═" * (inner_width + 2) + "╝\n")

        # Устанавливаем куку и отправляем на 2FA
        handler.send_response(302)
        handler.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly")
        handler.send_header("Location", "/2fa")
        handler.end_headers()
    else:
        print(f"[AUTH] ОШИБКА: Неверный пароль для {login_val}")
        handler.redirect("/")


def verify(handler, data):
    cookie_header = handler.headers.get("Cookie", "")
    session_id = None
    if "session_id=" in cookie_header:
        # Извлекаем ID сессии корректно
        parts = cookie_header.split("session_id=")
        if len(parts) > 1:
            session_id = parts[1].split(";")[0].strip()

    input_code = data.get("code", [""])[0].strip()

    if session_id and session_id in handler.__class__.sessions:
        correct_code = handler.__class__.codes.get(session_id)

        print(f"[2FA] Проверка: введено '{input_code}', ожидалось '{correct_code}'")

        if input_code == correct_code:
            # Авторизация подтверждена
            handler.__class__.sessions[session_id]["2fa"] = True

            user_data = handler.__class__.sessions[session_id]["user"]
            username = user_data.get("login")
            role = user_data.get("role")

            # Удаляем временный код
            if session_id in handler.__class__.codes:
                del handler.__class__.codes[session_id]

            # ГИБКОЕ РАЗДЕЛЕНИЕ ПУТЕЙ
            # Проверяем либо по логину 'admin', либо по роли 'Администратор'
            if username == "admin" or role == "Администратор":
                print(f"[2FA] УСПЕХ! Админ вошел.")
                handler.redirect("/dashboard")
            else:
                print(f"[2FA] УСПЕХ! Пользователь {username} вошел.")
                # Если у тебя нет страницы /orders, замени на нужную (например /shop)
                handler.redirect("/orders")
        else:
            print("[2FA] ОШИБКА: Код не совпал.")
            handler.redirect("/2fa?error=1")
    else:
        print("[2FA] Ошибка: сессия не найдена или истекла.")
        handler.redirect("/")


def logout(handler):
    cookie_header = handler.headers.get("Cookie", "")
    session_id = None
    if "session_id=" in cookie_header:
        parts = cookie_header.split("session_id=")
        if len(parts) > 1:
            session_id = parts[1].split(";")[0].strip()

    if session_id:
        if session_id in handler.__class__.sessions:
            del handler.__class__.sessions[session_id]
        if session_id in handler.__class__.codes:
            del handler.__class__.codes[session_id]

    handler.send_response(302)
    handler.send_header("Set-Cookie", "session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
    handler.send_header("Location", "/")
    handler.end_headers()