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

    # Поддерживаем и словари, и кортежи для данных пользователя
    admin_name = user.get("login") if isinstance(user, dict) else user[1]

    html = html.replace("{{ADMIN_NAME}}", str(admin_name))
    html = html.replace("{{CONTENT}}", "")

    handler.send_response(200)
    handler.send_header("Content-type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode("utf-8"))


def show_buy_page(handler):
    """Отображает страницу покупки лицензий (buy.html)"""
    try:
        licenses = get_all_licenses()

        # Пытаемся получить историю покупок
        try:
            from models.purchase_model import get_all_purchases
            purchases = get_all_purchases()
        except ImportError:
            print("Предупреждение: модель purchase_model не найдена")
            purchases = []

    except Exception as e:
        print(f"Ошибка БД при загрузке страницы покупок: {e}")
        licenses, purchases = [], []

    # Генерация строк для таблицы доступных лицензий
    lic_rows = ""
    if not licenses:
        lic_rows = "<tr><td colspan='5' style='text-align:center; padding:10px;'>Нет доступных лицензий</td></tr>"
    else:
        for l in licenses:
            lic_rows += f"""
            <tr>
                <td style="padding:10px; text-align:center;">{l[0]}</td>
                <td style="padding:10px;">{l[1]}</td>
                <td style="padding:10px; text-align:center;">{l[2]}</td>
                <td style="padding:10px; text-align:center;">{l[3]} дн.</td>
                <td style="padding:10px; text-align:center;">
                    <a href="/buy?license_id={l[0]}" 
                       style="background:#28a745; color:white; padding:5px 10px; text-decoration:none; border-radius:3px; font-weight:bold;">
                       Купить
                    </a>
                </td>
            </tr>
            """

    # Генерация строк для таблицы истории покупок
    pur_rows = ""
    if not purchases:
        pur_rows = "<tr><td colspan='3' style='text-align:center; padding:10px;'>История покупок пуста</td></tr>"
    else:
        for p in purchases:
            pur_rows += f"""
            <tr>
                <td style="padding:10px; text-align:center;">{p[0]}</td>
                <td style="padding:10px; text-align:center;">{p[1]}</td>
                <td style="padding:10px; text-align:center;">{p[2]}</td>
            </tr>
            """

    render_template(handler, "templates/purchases.html", {
        "{{LICENSE_ROWS}}": lic_rows,
        "{{PURCHASE_ROWS}}": pur_rows
    })


def show_products(handler):
    """Отображает страницу со списком ПО"""
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
                    <a href="/delete_product?id={p[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold;" 
                       onclick="return confirm('Удалить товар ID {p[0]}?')">[удалить]</a>
                </td>
            </tr>
            """
    render_template(handler, "templates/products.html", {"{{TABLE_ROWS}}": rows_html})


def show_licenses(handler):
    """Отображает таблицу лицензий"""
    try:
        licenses = get_all_licenses()
    except Exception as e:
        print(f"Ошибка БД: {e}")
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
                    <a href="/delete_license?id={l[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold;" 
                       onclick="return confirm('Удалить лицензию ID {l[0]}?')">[удалить]</a>
                </td>
            </tr>
            """
    render_template(handler, "templates/licenses.html", {"{{TABLE_ROWS}}": rows_html})


def show_keys(handler):
    """Отображает таблицу ключей активации"""
    try:
        from models.key_model import get_all_keys
        keys = get_all_keys()
    except Exception as e:
        print(f"Ошибка БД: {e}")
        keys = []

    rows_html = ""
    if not keys:
        rows_html = "<tr><td colspan='6' style='text-align:center; padding:20px;'>Ключи не найдены</td></tr>"
    else:
        for k in keys:
            status_color = "#28a745" if k[4] == 'Активен' else ("#fd7e14" if k[4] == 'Заблокирован' else "#6c757d")
            rows_html += f"""
            <tr>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{k[0]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px;">{k[1]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">{k[2]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; font-family: monospace;">{k[3]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center; color: {status_color}; font-weight: bold;">{k[4]}</td>
                <td style="border: 1px solid #adb5bd; padding: 10px; text-align: center;">
                    <a href="/change_key_status?id={k[0]}&status=Заблокирован" style="color: #fd7e14; text-decoration: none; font-size: 11px;">[блок]</a>
                    <a href="/change_key_status?id={k[0]}&status=Активен" style="color: #28a745; text-decoration: none; font-size: 11px; margin-left: 5px;">[акт]</a>
                    <a href="/delete_key?id={k[0]}" style="color: #dc3545; text-decoration: none; font-weight: bold; margin-left: 10px;">[X]</a>
                </td>
            </tr>
            """
    render_template(handler, "templates/keys.html", {"{{TABLE_ROWS}}": rows_html})


def render_template(handler, template_path, replacements):
    """Вспомогательная функция для рендеринга HTML"""
    if not os.path.exists(template_path):
        handler.send_error(404, f"Template not found: {template_path}")
        return

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()

        for key, value in replacements.items():
            html = html.replace(str(key), str(value))

        handler.send_response(200)
        handler.send_header("Content-type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(html.encode("utf-8"))
    except Exception as e:
        print(f"Render Error: {e}")
        if not handler.wfile.closed:
            handler.send_error(500, "Internal Server Error")