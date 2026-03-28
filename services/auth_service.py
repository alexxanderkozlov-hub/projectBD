from models.user_model import find_user_by_login
from utils.hash import check_password
from services.twofa_service import generate_code

def login_user(login, password):
    user = find_user_by_login(login)

    if not user:
        return None, "Пользователь не найден"

    if not check_password(password, user["password"]):
        return None, "Неверный пароль"

    # генерируем 2FA
    generate_code(user["id"])

    return user, None