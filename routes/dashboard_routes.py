import os
from models.product_model import get_all_products
from models.license_model import get_all_licenses


def dashboard(handler):
    """Отображает главное меню (сетку кнопок)"""
    user = handler.get_user()
    if not user:
        handler.redirect("/")
        return

    template_path = "templates/admin_dashboard.html"
    if not os.path.exists(template_path):
        handler.send_error(404, "Шаблон дашборда не найден")
        return

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        handler.send_error(500, f"Ошибка чтения шаблона: {e}")
        return

    # Подставляем логин администратора
    html = html.replace("{{ADMIN_NAME}}", user.get("login", "Администратор"))
    html = html.replace("{{CONTENT}}", "")

    handler.send_response(200)
    handler.send_header("Content-type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode("utf-8"))


def show_products(handler):
    """Отображает страницу со списком ПО и кнопками управления (CRUD)"""
    try:
        products = get_all_products()
    except Exception as e:
        print(f"Ошибка БД: {e}")
        products = []

    rows_html = ""
    if not products:
        rows_html = "<tr><td colspan='5' style='text-align:center; padding:20px;'>Товары не найдены</td></tr>"
    else:
        for p in products:
            rows_html += f"""
            <tr>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{p[0]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px;">{p[1]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: right;">{p[3]} ₽</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{p[2]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">
                    <a href="/edit_product?id={p[0]}" style="color: #28a745; text-decoration: none; font-weight: bold; margin-right: 10px;">[изменить]</a>
                    <a href="/delete_product?id={p[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold;" 
                       onclick="return confirm('Удалить товар ID {p[0]}?')">[удалить]</a>
                </td>
            </tr>
            """

    render_template(handler, "templates/products.html", {"{{TABLE_ROWS}}": rows_html})


def show_licenses(handler):
    """Отображает таблицу лицензий с кнопками управления"""
    try:
        licenses = get_all_licenses()
    except Exception as e:
        print(f"Ошибка БД при получении лицензий: {e}")
        licenses = []

    rows_html = ""
    if not licenses:
        rows_html = "<tr><td colspan='5' style='text-align:center; padding:20px;'>Лицензий нет</td></tr>"
    else:
        for l in licenses:
            rows_html += f"""
            <tr>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{l[0]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px;">{l[1]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{l[2]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{l[3]} дн.</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">
                    <a href="/edit_license?id={l[0]}" style="color: #28a745; text-decoration: none; font-weight: bold; margin-right: 10px;">[изменить]</a>
                    <a href="/delete_license?id={l[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold;" 
                       onclick="return confirm('Удалить лицензию ID {l[0]}?')">[удалить]</a>
                </td>
            </tr>
            """

    render_template(handler, "templates/licenses.html", {"{{TABLE_ROWS}}": rows_html})


def show_keys(handler):
    """Отображает таблицу ключей активации с функциями управления статусом"""
    try:
        from models.key_model import get_all_keys
        keys = get_all_keys()
    except Exception as e:
        print(f"Ошибка БД при получении ключей: {e}")
        keys = []

    rows_html = ""
    if not keys:
        rows_html = "<tr><td colspan='6' style='text-align:center; padding:20px;'>Ключи не найдены</td></tr>"
    else:
        for k in keys:
            # k[0]=id, k[1]=prod_name, k[2]=lic_type, k[3]=license_key, k[4]=status

            # Настройка цвета текста в зависимости от статуса
            if k[4] == 'Активен':
                status_style = "color: #28a745; font-weight: bold;"
            elif k[4] == 'Заблокирован':
                status_style = "color: #fd7e14; font-weight: bold;"
            else:  # Истек
                status_style = "color: #6c757d; font-weight: bold;"

            rows_html += f"""
            <tr>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{k[0]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px;">{k[1]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{k[2]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; font-family: monospace;">{k[3]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center; {status_style}">{k[4]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">
                    <div style="display: flex; flex-direction: column; gap: 5px;">
                        <div>
                            <a href="/change_key_status?id={k[0]}&status=Заблокирован" style="color: #fd7e14; text-decoration: none; font-size: 12px;">[блок]</a>
                            <a href="/change_key_status?id={k[0]}&status=Истек" style="color: #6c757d; text-decoration: none; font-size: 12px; margin-left: 5px;">[истек]</a>
                            <a href="/change_key_status?id={k[0]}&status=Активен" style="color: #28a745; text-decoration: none; font-size: 12px; margin-left: 5px;">[акт]</a>
                        </div>
                        <a href="/delete_key?id={k[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold;" 
                           onclick="return confirm('Удалить ключ ID {k[0]}?')">[удалить]</a>
                    </div>
                </td>
            </tr>
            """

    render_template(handler, "templates/keys.html", {"{{TABLE_ROWS}}": rows_html})


def render_template(handler, template_path, replacements):
    """Вспомогательная функция для рендеринга HTML"""
    if not os.path.exists(template_path):
        # Используем английский текст для избежания UnicodeEncodeError в заголовках сервера
        handler.send_error(404, f"Template not found: {template_path}")
        return

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        for key, value in replacements.items():
            html = html.replace(key, value)

        handler.send_response(200)
        handler.send_header("Content-type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(html.encode("utf-8"))
    except Exception as e:
        print(f"Render Error: {e}")
        handler.send_error(500, "Internal Server Error")