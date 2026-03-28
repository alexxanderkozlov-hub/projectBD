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
            # p[0]-id, p[1]-name, p[2]-version, p[3]-price
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

    template_path = "templates/products.html"
    if not os.path.exists(template_path):
        handler.send_error(404, "Файл templates/products.html не найден")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{TABLE_ROWS}}", rows_html)

    handler.send_response(200)
    handler.send_header("Content-type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode("utf-8"))


def show_licenses(handler):
    """Отображает таблицу лицензий с кнопками управления"""
    try:
        licenses = get_all_licenses()
    except Exception as e:
        print(f"Ошибка БД при получении лицензий: {e}")
        licenses = []

    rows_html = ""

    if not licenses:
        # Увеличили colspan до 5, так как добавили колонку действий
        rows_html = "<tr><td colspan='5' style='text-align:center; padding:20px;'>Лицензий нет</td></tr>"
    else:
        for l in licenses:
            # l[0]=id, l[1]=название продукта (из JOIN), l[2]=тип, l[3]=дни
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

    template_path = "templates/licenses.html"
    if not os.path.exists(template_path):
        handler.send_error(404, f"Шаблон {template_path} не найден")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{TABLE_ROWS}}", rows_html)

    handler.send_response(200)
    handler.send_header("Content-type", "text/html; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(html.encode("utf-8"))