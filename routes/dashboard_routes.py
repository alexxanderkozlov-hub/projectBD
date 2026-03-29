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
                # Проверяем, как приходят данные (словари или кортежи)
                if isinstance(p, dict):
                    pid, u_id, l_id, pdate = p.get('id'), p.get('user_id'), p.get('license_id'), p.get('date')
                else:
                    pid, u_id, l_id, pdate = p[0], p[1], p[2], p[3]

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
            from models.license_model import get_licenses_with_products
            available_items = get_licenses_with_products()
        except Exception as e:
            print(f"Ошибка загрузки товаров из БД: {e}")
            available_items = []

def show_buy_page(handler):
            """ГЛАВНЫЙ ЭКРАН: Разделение на Админ-лог (purchases.html) и Магазин (user_shop.html)"""
            user = handler.get_user()
            if not user:
                handler.redirect("/")
                return

            # Определяем данные текущего пользователя
            current_user_id = user.get("id") if isinstance(user, dict) else user[0]
            current_user_login = user.get("login") if isinstance(user, dict) else user[1]

            # === ЛОГИКА ДЛЯ АДМИНА (Просмотр транзакций) ===
            if current_user_login == "admin":
                try:
                    from models.purchase_model import get_all_purchases
                    all_purchases = get_all_purchases()
                except Exception as e:
                    print(f"Ошибка загрузки транзакций: {e}")
                    all_purchases = []

                pur_rows = ""
                if not all_purchases:
                    pur_rows = "<tr><td colspan='5' class='text-center'>Транзакции не найдены</td></tr>"
                else:
                    for p in all_purchases:
                        # p[0]-ID покупки, p[1]-User ID, p[2]-Lic ID, p[3]-Дата
                        # Если в get_all_purchases используется JOIN, индексы могут быть другими
                        pid = p.get('id') or p.get('purchase_id')
                        uid = p.get('user_id')
                        lid = p.get('license_id')
                        pdate = p.get('date') or p.get('purchase_date')

                        pur_rows += f"""
                        <tr>
                            <td class="text-center">{pid}</td>
                            <td class="text-center">User #{uid}</td>
                            <td class="text-center">Пакет #{lid}</td>
                            <td class="text-center">{pdate}</td>
                            <td class="text-center">
                                <a href="/delete_purchase?id={pid}" 
                                   style="color: #dc3545; text-decoration: none; font-weight: bold;"
                                   onclick="return confirm('Удалить запись о покупке?');">
                                   [удалить]
                                </a>
                            </td>
                        </tr>"""

                render_template(handler, "templates/purchases.html", {
                    "{{PURCHASE_ROWS}}": pur_rows
                })

            # === ЛОГИКА ДЛЯ ПОЛЬЗОВАТЕЛЯ (Магазин) ===
            else:
                try:
                    from models.license_model import get_licenses_with_products
                    available_items = get_licenses_with_products()
                except Exception as e:
                    print(f"Ошибка загрузки магазина: {e}")
                    available_items = []

                shop_rows = ""
                if not available_items:
                    shop_rows = "<tr><td colspan='6' class='text-center'>Товары временно отсутствуют</td></tr>"
                else:
                    # Используем enumerate, где 'i' — это порядковый номер (начиная с 1)
                    # а 'item' — это данные из твоей базы данных
                    for i, item in enumerate(available_items, 1):
                        # Структура из БД: (license_id, product_name, license_type, duration, price)
                        real_db_id = item[0]  # Настоящий ID лицензии (например, 15 или 42)
                        name = item[1]
                        l_type = item[2]
                        days = item[3]
                        price = item[4]

                        shop_rows += f"""
                                <tr>
                                    <td class="text-center">{i}</td>

                                    <td><strong>{name}</strong></td>
                                    <td>{l_type}</td>
                                    <td class="text-center">{days} дней</td>
                                    <td class="text-center">{price} ₽</td>
                                    <td class="text-center">
                                        <form action="/buy" method="POST" class="buy-form" style="margin:0;">
                                            <input type="hidden" name="license_id" value="{real_db_id}">
                                            <button type="submit" class="btn-buy">Купить</button>
                                        </form>
                                    </td>
                                </tr>
                                """

                # Используем твой новый шаблон user_shop.html
                render_template(handler, "templates/user_shop.html", {
                    "{{TABLE_ROWS}}": shop_rows
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
        # p[0]-ID, p[1]-Название, p[2]-Версия, p[3]-Цена
        rows += f"""
        <tr>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{p[0]}</td>
            <td style="border:1px solid #adb5bd; padding:10px;">{p[1]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:right;">{p[3]} ₽</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{p[2]}</td>
            <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">
                <a href="/edit_product?id={p[0]}" 
                   style="color:#007bff; font-weight:bold; text-decoration:none; margin-right:10px;">[изменить]</a>

                <a href="/delete_product?id={p[0]}" 
                   style="color:#dc3545; font-weight:bold; text-decoration:none;" 
                   onclick="return confirm('Вы уверены, что хотите удалить {p[1]}?')">[удалить]</a>
            </td>
        </tr>"""
    render_template(handler, "templates/products.html", {"{{TABLE_ROWS}}": rows})


def show_licenses(handler):
    """Управление лицензиями (Админ)"""

    try:
        from models.license_model import get_all_licenses
        licenses = get_all_licenses()
    except Exception as e:
        print("Ошибка получения лицензий:", e)
        licenses = []

    rows = ""

    if not licenses:
        rows = "<tr><td colspan='5' style='text-align:center; padding:20px;'>Нет данных</td></tr>"
    else:
        for l in licenses:
            # Предполагаем структуру: (ID, Product_Name, Type, Duration)
            license_id = l[0]
            product_name = l[1]
            license_type = l[2]
            duration = l[3]

            rows += f"""
            <tr>
                <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{license_id}</td>
                <td style="border:1px solid #adb5bd; padding:10px;">{product_name}</td>
                <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{license_type}</td>
                <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">{duration} дн.</td>
                <td style="border:1px solid #adb5bd; padding:10px; text-align:center;">
                    <a href="/edit_license?id={license_id}" 
                       style="color:#007bff; font-weight:bold; text-decoration:none; margin-right:10px;">
                        [изменить]
                    </a>

                    <a href="/delete_license?id={license_id}" 
                       style="color:#dc3545; font-weight:bold; text-decoration:none;"
                       onclick="return confirm('Удалить этот тип лицензии?')">
                        [удалить]
                    </a>
                </td>
            </tr>
            """

    # Вызываем рендер шаблона
    from routes.dashboard_routes import render_template
    render_template(handler, "templates/licenses.html", {
        "{{TABLE_ROWS}}": rows
    })

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