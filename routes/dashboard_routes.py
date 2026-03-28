import os


def dashboard(handler):
    # 1. Проверка авторизации (через сессию)
    user = handler.get_user()
    if not user:
        handler.redirect("/")
        return

    # 2. Путь к шаблону
    template_path = "templates/admin_dashboard.html"

    if not os.path.exists(template_path):
        handler.send_error(404, "Шаблон дашборда не найден")
        return

    # 3. Читаем HTML
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 4. Заменяем только имя администратора.
    # Всю логику с {{CONTENT}} и переменной tab мы убираем,
    # чтобы под кнопками ничего не вылезало.
    html = html.replace("{{ADMIN_NAME}}", user.get("login", "Администратор"))

    # Если в твоем шаблоне admin_dashboard.html осталась метка {{CONTENT}},
    # мы заменяем её на пустую строку, чтобы она не мозолила глаза.
    html = html.replace("{{CONTENT}}", "")

    # 5. Отправка чистого дашборда
    handler.send_response(200)
    handler.send_header("Content-type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode("utf-8"))