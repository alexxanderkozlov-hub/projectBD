import os
import urllib.parse
from models.product_model import get_all_products
from models.license_model import get_all_licenses

def dashboard(handler):
    """Отображает главное меню (сетку кнопок) для Админа"""
    user = handler.get_user()
    if not user:
        handler.redirect("/")
        return

    admin_name = user.get("login") if isinstance(user, dict) else user[1]

    render_template(handler, "templates/admin_dashboard.html", {
        "{{ADMIN_NAME}}": str(admin_name),
        "{{CONTENT}}": ""
    })

def show_buy_page(handler):
    """ГЛАВНЫЙ ЭКРАН: Разделение на Админ-лог (purchases.html) и Магазин (user_shop.html)"""
    user = handler.get_user()
    if not user:
        handler.redirect("/")
        return

    # Получаем данные текущего пользователя
    current_user_id = user.get("id") if isinstance(user, dict) else user[0]
    current_user_login = user.get("login") if isinstance(user, dict) else user[1]

    # === ЛОГИКА ДЛЯ АДМИНА (Просмотр всех транзакций + Удаление) ===
    if current_user_login == "admin":
        try:
            from models.purchase_model import get_all_purchases
            all_purchases = get_all_purchases()
        except Exception as e:
            print(f"Ошибка загрузки данных транзакций: {e}")
            all_purchases = []

        pur_rows = ""
        if not all_purchases:
            pur_rows = "<tr><td colspan='5' style='border:1px solid #dee2e6; padding:15px; text-align:center;'>Транзакции не найдены</td></tr>"
        else:
            for p in all_purchases:
                pid = p.get('id')
                u_id = p.get('user_id')
                l_id = p.get('license_id')
                pdate = p.get('date')

                pur_rows += f"""
                <tr>
                    <td style="border:1px solid #dee2e6; padding:12px; text-align:center;">{pid}</td>
                    <td style="border:1px solid #dee2e6; padding:12px; text-align:center;">{u_id}</td>
                    <td style="border:1px solid #dee2e6; padding:12px; text-align:center;">{l_id}</td>
                    <td style="border:1px solid #dee2e6; padding:12px; text-align:center;">{pdate}</td>
                    <td style="border:1px solid #dee2e6; padding:12px; text-align:center;">
                        <a href="/delete_purchase?id={pid}" 
                           style="color: #dc3545; text-decoration: none; font-weight: bold; font-size: 13px;"
                           onclick="return confirm('Удалить эту транзакцию из истории?');">
                           [удалить]
                        </a>
                    </td>
                </tr>"""

        render_template(handler, "templates/purchases.html", {
            "{{PURCHASE_ROWS}}": pur_rows
        })

    # === ЛОГИКА ДЛЯ ОБЫЧНОГО ПОЛЬЗОВАТЕЛЯ (Магазин с данными из БД) ===
    else:
        try:
            # Используем новую функцию, которая делает JOIN таблиц
            from models.license_model import get_licenses_with_products
            available_items = get_licenses_with_products()
        except Exception as e:
            print(f"Ошибка загрузки товаров из БД: {e}")
            available_items = []

        shop_rows = ""
        if not available_items:
            shop_rows = "<tr><td colspan='4' style='padding:20px; text-align:center;'>Товары временно отсутствуют</td></tr>"
        else:
            for item in available_items:
                # item[0]=Название продукта, item[1]=Тип лицензии, item[2]=Дни, item[3]=ID лицензии
                product_name = item[0]
                license_name = item[1]
                duration = item[2]
                lic_id = item[3]

                shop_rows += f"""
                <tr>
                    <td style="border-bottom:1px solid #eee; padding:15px;">{product_name}</td>
                    <td style="border-bottom:1px solid #eee; padding:15px;">{license_name}</td>
                    <td style="border-bottom:1px solid #eee; padding:15px;">{duration} дней</td>
                    <td style="border-bottom:1px solid #eee; padding:15px; text-align:right;">
                        <a href="/buy?license_id={lic_id}" 
                           style="background:#28a745; color:white; padding:8px 15px; border-radius:4px; text-decoration:none; font-weight:bold; font-size:13px;">
                           Купить
                        </a>
                    </td>
                </tr>"""

        render_template(handler, "templates/user_shop.html", {
            "{{SHOP_ROWS}}": shop_rows
        })

def show_keys(handler):
    """Управление ключами (Админ)"""
    try:
        from models.key_model import get_all_keys
        keys = get_all_keys()
    except Exception as e:
        print(f"Ошибка получения ключей: {e}")
        keys = []

    rows = ""
    for k in keys:
        status = k[4]
        status_color = "#28a745" if status == 'Активен' else "#dc3545"
        next_status = "Заблокирован" if status == "Активен" else "Активен"
        action_label = "заблокировать" if status == "Активен" else "активировать"

        rows += f"""
        <tr>
            <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">{k[0]}</td>
            <td style="padding: 15px; border: 1px solid #dee2e6;">{k[1]}</td>
            <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">{k[2]}</td>
            <td style="padding: 15px; border: 1px solid #dee2e6; font-family: monospace;">{k[3]}</td>
            <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center; color: {status_color}; font-weight: bold;">{status}</td>
            <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">
                <a href="/change_key_status?id={k[0]}&status={next_status}" 
                   style="color: #007bff; text-decoration: none; font-size: 13px; margin-right: 10px;">[{action_label}]</a>
                <a href="/delete_key?id={k[0]}" 
                   style="color: #dc3545; text-decoration: none; font-size: 13px; font-weight: bold;">[удалить]</a>
            </td>
        </tr>"""

    if not rows:
        rows = "<tr><td colspan='6' style='padding:20px; text-align:center;'>Ключи не найдены</td></tr>"

    render_template(handler, "templates/keys.html", {"{{TABLE_ROWS}}": rows})

def show_products(handler):
    """Управление ПО (Админ)"""
    products = get_all_products()
    rows = ""
    for p in products:
        rows += f"""
        <tr>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{p[0]}</td>
            <td style="border:1px solid #adb5bd; padding:10px;">{p[1]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:right;">{p[3]} ₽</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{p[2]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">
                <a href="/delete_product?id={p[0]}" style="color:#dc3545; font-weight:bold; text-decoration:none;">[удалить]</a>
            </td>
        </tr>"""
    render_template(handler, "templates/products.html", {"{{TABLE_ROWS}}": rows})

def show_licenses(handler):
    """Управление типами лицензий (Админ)"""
    licenses = get_all_licenses()
    rows = ""
    for l in licenses:
        rows += f"""
        <tr>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{l[0]}</td>
            <td style="border:1px solid #adb5bd; padding:10px;">{l[1]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{l[2]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{l[3]} дн.</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">
                <a href="/delete_license?id={l[0]}" style="color:#dc3545; font-weight:bold; text-decoration:none;">[удалить]</a>
            </td>
        </tr>"""
    render_template(handler, "templates/licenses.html", {"{{TABLE_ROWS}}": rows})

def render_template(handler, template_path, replacements):
    """Универсальный загрузчик HTML шаблонов"""
    if not os.path.exists(template_path):
        handler.send_error(404, f"Template {template_path} not found")
        return

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        for placeholder, value in replacements.items():
            content = content.replace(str(placeholder), str(value))

        handler.send_response(200)
        handler.send_header("Content-type", "text/html; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(content.encode("utf-8"))
    except Exception as e:
        print(f"Ошибка рендеринга: {e}")
        handler.send_error(500)