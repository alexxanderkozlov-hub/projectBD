from http.server import BaseHTTPRequestHandler
import urllib.parse
import os

from routes.auth_routes import login, verify
# Добавь show_buy_page в импорт!
from routes.dashboard_routes import dashboard, show_buy_page, show_products, show_licenses, show_keys


class MyHandler(BaseHTTPRequestHandler):
    sessions = {}
    codes = {}

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        print(f"--- GET запрос: {path} ---")

        # 1. ПУБЛИЧНЫЕ РОУТЫ (Доступны всем без входа)
        if path == "/":
            return self.render("templates/login.html")

        if path.startswith("/static/"):
            return self.serve_static()

        if path == "/favicon.ico":
            self.send_response(204)
            return self.end_headers()

        # 2. РОУТ ВЫХОДА
        elif path == "/logout":
            from routes.auth_routes import logout
            return logout(self)

        # 3. ПРОВЕРКА СЕССИИ ДЛЯ 2FA
        if path == "/2fa":
            if not self.get_session():
                return self.redirect("/")

            # ЛОГИКА ОШИБКИ: Проверяем параметр error в URL
            error_msg = ""
            if query.get("error") == ["1"]:
                # Этот текст подставится вместо {{ERROR}} в шаблоне
                error_msg = '<p style="color: #e74c3c; font-size: 14px; margin-top: 10px; font-weight: bold;">Код введен неверно. Попробуйте снова.</p>'

            return self.render("templates/2fa.html", {"{{ERROR}}": error_msg})

        # 4. ЗАКРЫТАЯ ЗОНА (Требует авторизации и пройденного 2FA)
        session = self.get_session()
        if not session or not session.get("2fa"):
            return self.redirect("/")

        # --- МАРШРУТЫ ДЛЯ АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---

        if path == "/dashboard":
            from routes.dashboard_routes import dashboard
            return dashboard(self)

        elif path == "/products":
            from routes.dashboard_routes import show_products
            return show_products(self)

        elif path == "/licenses":
            from routes.dashboard_routes import show_licenses
            return show_licenses(self)

        elif path == "/keys":
            from routes.dashboard_routes import show_keys
            return show_keys(self)

        elif path == "/orders":
            # Страница магазина или список транзакций (зависит от роли внутри функции)
            from routes.dashboard_routes import show_buy_page
            return show_buy_page(self)

        # Обработка нажатия на кнопку "Купить" (если через GET)
        elif path == "/purchase":
            lic_id = query.get("license_id", [None])[0]
            return self.handle_purchase_logic(lic_id)

        # ===== УДАЛЕНИЕ (ADMIN ONLY) =====

        elif path == "/delete_purchase":
            pur_id = query.get("id", [None])[0]
            if pur_id:
                from models.purchase_model import delete_purchase
                delete_purchase(pur_id)
            return self.redirect("/orders")

        elif path == "/delete_product":
            p_id = query.get("id", [None])[0]
            if p_id:
                from models.product_model import delete_product_by_id
                delete_product_by_id(p_id)
            return self.redirect("/products")

        elif path == "/delete_license":
            l_id = query.get("id", [None])[0]
            if l_id:
                from models.license_model import delete_license_by_id
                delete_license_by_id(l_id)
            return self.redirect("/licenses")

        elif path == "/delete_key":
            k_id = query.get("id", [None])[0]
            if k_id:
                from models.key_model import delete_key_by_id
                delete_key_by_id(k_id)
            return self.redirect("/keys")

            # 2. ИЗМЕНЕНИЕ СТАТУСОВ И РЕДАКТИРОВАНИЕ

        elif path == "/change_key_status":
            k_id = query.get("id", [None])[0]
            status = query.get("status", [None])[0]
            if k_id and status:
                from models.key_model import update_key_status
                update_key_status(k_id, status)
            return self.redirect("/keys")


        elif path == "/edit_product":
            p_id = query.get("id", [None])[0]
            if p_id:
                from models.product_model import get_product_by_id
                product = get_product_by_id(p_id)
                if product:
                    # Передаем данные в шаблон редактирования

                    return self.render("templates/edit_product.html", {
                        "{{ID}}": str(product[0]),
                        "{{NAME}}": str(product[1]),
                        "{{VERSION}}": str(product[2]),
                        "{{PRICE}}": str(product[3])
                    })
            return self.redirect("/products")

            # ===== РЕДАКТИРОВАНИЕ ЛИЦЕНЗИИ (GET) =====
        elif path == "/edit_license":
            l_id = query.get("id", [None])[0]
            if l_id:
                from models.license_model import get_license_by_id
                from models.product_model import get_all_products

                lic = get_license_by_id(l_id)  # Получаем: (id, prod_id, type, duration)
                products = get_all_products()

                if lic:
                    # 1. Генерируем опции для списка продуктов
                    options = ""
                    current_prod_id = lic[1]
                    for p in products:
                        # Сравниваем ID как строки для надежности
                        selected = "selected" if str(p[0]) == str(current_prod_id) else ""
                        options += f'<option value="{p[0]}" {selected}>{p[1]} (v.{p[2]})</option>'

                    # 2. Рендерим шаблон с правильными ключами из твоего HTML
                    return self.render("templates/edit_license.html", {
                        "{{ID}}": str(lic[0]),
                        "{{PRODUCT_OPTIONS}}": options,  # Должно совпадать с HTML!
                        "{{DURATION}}": str(lic[3])  # Должно совпадать с HTML!
                    })
            return self.redirect("/licenses")

        # ===== ДОБАВЛЕНИЕ (Страницы) =====
        elif path == "/add_product":
            return self.render("templates/add_product.html")

        elif path == "/add_license":
            from models.product_model import get_all_products
            products = get_all_products()
            try:
                with open("templates/add_license.html", "r", encoding="utf-8") as f:
                    html = f.read()
                # p[0] - ID, p[1] - Название продукта
                options = "".join([f'<option value="{p[0]}">{p[1]} (v.{p[2]})</option>' for p in products])
                return self.send_html(html.replace("{{PRODUCT_OPTIONS}}", options))
            except Exception as e:
                return self.send_error(500, f"Ошибка загрузки шаблона: {e}")

        elif path == "/add_key":
            # Используем функцию с JOIN, чтобы видеть какой продукт к какой лицензии
            from models.license_model import get_all_licenses
            lics = get_all_licenses()
            try:
                with open("templates/add_key.html", "r", encoding="utf-8") as f:
                    html = f.read()
                # l[1] - название продукта, l[2] - тип лицензии, l[0] - ID лицензии
                options = "".join([f'<option value="{l[0]}">{l[1]} ({l[2]}) - ID:{l[0]}</option>' for l in lics])
                return self.send_html(html.replace("{{LICENSE_OPTIONS}}", options))
            except Exception as e:
                return self.send_error(500, f"Ошибка загрузки шаблона: {e}")

        else:
            return self.send_error(404, f"Путь {path} не найден")

    def do_POST(self):
        import urllib.parse
        import json
        import re
        import injections.task_1 as t1
        import injections.task_2 as t2
        import injections.task_3 as t3
        import injections.task_4 as t4
        import injections.task_5 as t5
        import injections.task_6 as t6
        import injections.task_7 as t7
        import injections.task_8 as t8  # ДОБАВИЛИ

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        path = self.path
        print(f"--- POST запрос: {path} ---")

        # =========================
        # ЗАДАНИЕ 4 (JSON API)
        # =========================
        if path == "/api/add_user":
            try:
                json_data = json.loads(body)
                u_id = json_data.get("id")
                name_val = json_data.get("name", "")

                use_safe = "safe" in name_val.lower()

                if use_safe:
                    msg, query_text, db_status = t4.run_task_4_safe(u_id, name_val)
                else:
                    msg, query_text, db_status = t4.run_task_4(u_id, name_val)

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()

                response = {
                    "title": "Задание №4: Инъекция в JSON API",
                    "mode": "Безопасно" if use_safe else "УЯЗВИМО",
                    "status": msg,
                    "sql_query": query_text,
                    "database_info": db_status
                }

                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return

            except Exception as e:
                self.send_error(400, f"Ошибка парсинга JSON: {str(e)}")
                return

        # =========================
        # FORM DATA
        # =========================
        data = urllib.parse.parse_qs(body)

        if path == "/login":
            login_val = data.get('login', [''])[0].strip()
            pass_val = data.get('password', [''])[0].strip()

            lv_up = login_val.upper()

            # ОПРЕДЕЛЕНИЕ ЗАДАНИЙ
            is_task_8 = "HEADER" in lv_up  # НОВОЕ ЗАДАНИЕ
            is_task_7 = "META" in lv_up
            is_task_6 = "PAGE" in lv_up
            is_task_5 = "CTE" in lv_up

            is_task_3 = not (is_task_5 or is_task_6 or is_task_7 or is_task_8) and (
                    "' OR '" in login_val or "' OR '" in pass_val)

            is_task_2 = not (is_task_5 or is_task_3 or is_task_6 or is_task_7 or is_task_8) and (
                    ";" in login_val or "DROP" in lv_up or "%" in login_val)

            is_task_1 = not (is_task_5 or is_task_3 or is_task_2 or is_task_6 or is_task_7 or is_task_8) and (
                    login_val.isdigit() or "OR" in lv_up)

            # ОБЩИЙ БЛОК
            if is_task_1 or is_task_2 or is_task_3 or is_task_5 or is_task_6 or is_task_7 or is_task_8:

                use_safe = (pass_val.lower() == "safe")
                status = "Обработка запроса"
                results = []

                # =========================
                # ЗАДАНИЕ 8 (HTTP HEADER)
                # =========================
                if is_task_8:
                    # Читаем заголовок User-Agent напрямую из self.headers
                    ua_value = self.headers.get('User-Agent', 'Unknown')

                    if use_safe:
                        _, query_text, status = t8.run_task_8_safe(ua_value)
                    else:
                        _, query_text, status = t8.run_task_8(ua_value)

                    title = "Задание №8: Инъекция через HTTP Header"
                    cols = ["Информация"]
                    results = [[f"Записанный User-Agent: {ua_value}"]]

                # =========================
                # ЗАДАНИЕ 7 (UNION METADATA)
                # =========================
                elif is_task_7:
                    clean_id = re.sub(r'(?i)META', '', login_val).strip()
                    if not clean_id: clean_id = "1"

                    if use_safe:
                        results, query_text, status = t7.run_task_7_safe(clean_id)
                    else:
                        results, query_text, status = t7.run_task_7(clean_id)

                    title = "Задание №7: UNION SQL Injection (метаданные)"
                    cols = ["ID", "Имя"]

                # =========================
                # ЗАДАНИЕ 6 (PAGINATION)
                # =========================
                elif is_task_6:
                    clean_params = re.sub(r'(?i)PAGE', '', login_val).strip()
                    parts = clean_params.split()
                    limit = parts[0] if len(parts) > 0 else "2"
                    offset = parts[1] if len(parts) > 1 else "0"

                    if use_safe:
                        results, query_text, status = t6.run_task_6_safe(limit, offset)
                    else:
                        results, query_text, status = t6.run_task_6(limit, offset)

                    title = "Задание №6: Пагинация (LIMIT/OFFSET)"
                    cols = ["ID", "Имя"]

                # =========================
                # ЗАДАНИЕ 5 (CTE)
                # =========================
                elif is_task_5:
                    clean_id = re.sub(r'(?i)CTE', '', login_val).strip()
                    if not clean_id: clean_id = "1"

                    if use_safe:
                        results, query_text, status = t5.run_task_5_safe(clean_id)
                    else:
                        results, query_text, status = t5.run_task_5(clean_id)

                    title = "Задание №5: CTE Injection"
                    cols = ["ID", "Информация"]

                # =========================
                # ЗАДАНИЕ 3
                # =========================
                elif is_task_3:
                    results, status, query_text = (
                        t3.run_task_3_safe(login_val, pass_val)
                        if use_safe else t3.run_task_3(login_val, pass_val)
                    )
                    title = "Задание №3: Обход авторизации"
                    cols = ["user_id", "role_id", "login", "password_hash", "totp_secret"]

                # =========================
                # ЗАДАНИЕ 2
                # =========================
                elif is_task_2:
                    results, status, query_text = (
                        t2.run_task_2_safe(login_val)
                        if use_safe else t2.run_task_2(login_val)
                    )
                    title = "Задание №2: LIKE + DROP"
                    cols = ["Найденные логины"]

                # =========================
                # ЗАДАНИЕ 1
                # =========================
                else:
                    results, query_text = (
                        t1.run_task_1_safe(login_val)
                        if use_safe else t1.run_task_1(login_val)
                    )
                    title = "Задание №1: Поиск по ID"
                    status = "Данные извлечены"
                    cols = ["user_id", "role_id", "login", "password_hash", "totp_secret"]

                # HTML ОТВЕТ (общий для всех заданий)
                color = "#4CAF50" if use_safe else "#f44336"
                rows = ""
                for r in results:
                    rows += "<tr>" + "".join([f"<td>{item}</td>" for item in r]) + "</tr>"

                response_html = f"""
                <html>
                <head><meta charset="UTF-8"><style>
                    body {{ font-family: sans-serif; padding: 20px; background: #f4f4f4; }}
                    .container {{ background: white; padding: 20px; border-radius: 10px;
                                  box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 900px; margin: auto; }}
                    .header {{ background: {color}; color: white; padding: 15px; border-radius: 5px; }}
                    .sql {{ background: #222; color: #0f0; padding: 15px; font-family: monospace;
                            border-radius: 5px; white-space: pre-wrap; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 10px; }}
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>{title}</h2>
                            <h3>Режим: {'Безопасно' if use_safe else 'УЯЗВИМО'}</h3>
                        </div>
                        <p><b>Статус:</b> {status}</p>
                        <p><b>SQL запрос:</b></p>
                        <div class="sql">{query_text}</div>
                        <table>
                            <thead><tr>{" ".join([f"<th>{c}</th>" for c in cols])}</tr></thead>
                            <tbody>
                                {rows if rows else "<tr><td colspan='10'>Нет данных</td></tr>"}
                            </tbody>
                        </table>
                        <br><a href="/">← Назад</a>
                    </div>
                </body></html>
                """
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(response_html.encode('utf-8'))
                return

            from routes.auth_routes import login
            return login(self, data)

        elif path == "/verify":
            from routes.auth_routes import verify
            return verify(self, data)

        session = self.get_session()
        if not session or not session.get("2fa"):
            return self.redirect("/")

        self.send_error(404, "Путь не найден")

    # Вспомогательный метод для обработки покупки
    def handle_purchase_logic(self, lic_id):
        """Связывает пользователя и лицензию в таблице purchases"""
        # 1. Проверяем, авторизован ли пользователь
        user = self.get_user()
        if not user:
            print("[SHOP] Ошибка: попытка покупки без авторизации")
            return self.redirect("/")

        try:
            # 2. Безопасное извлечение user_id
            # Проверяем все возможные варианты хранения (словарь 'id', словарь 'user_id' или кортеж)
            if isinstance(user, dict):
                user_id = user.get("id") or user.get("user_id")
            else:
                user_id = user[0]

            if not user_id:
                raise ValueError("ID пользователя не найден в данных сессии")

            # 3. Валидация ID лицензии
            if not lic_id:
                return self.send_error(400, "ID лицензии не передан")

            license_id_int = int(lic_id)

            # 4. Запись в базу данных
            from models.purchase_model import make_purchase

            if make_purchase(user_id, license_id_int):
                print(f"[SUCCESS] Покупка оформлена: User {user_id} купил License {license_id_int}")

                # 5. РЕДИРЕКТ: Обычного пользователя всегда возвращаем в магазин (/orders)
                # Админа теоретически можно кинуть в /keys, но для единообразия лучше тоже в /orders
                self.redirect("/orders")
            else:
                print(f"[DB ERROR] Не удалось записать покупку в базу: User {user_id}, Lic {lic_id}")
                self.send_error(500, "Ошибка базы данных при оформлении покупки")

        except ValueError as ve:
            print(f"[ERROR] Ошибка данных (возможно lic_id не число): {ve}")
            self.send_error(400, "Некорректные данные запроса")
        except Exception as e:
            print(f"[CRITICAL ERROR] Ошибка в handle_purchase_logic: {e}")
            self.send_error(500, f"Внутренняя ошибка сервера: {str(e)}")

    # --- СТАНДАРТНЫЕ МЕТОДЫ ---
    def get_session(self):
        cookie_header = self.headers.get("Cookie", "")
        if "session_id=" not in cookie_header: return None
        try:
            sid = cookie_header.split("session_id=")[1].split(";")[0].strip()
            return MyHandler.sessions.get(sid)
        except:
            return None

    def get_user(self):
        s = self.get_session()
        return s.get("user") if s else None

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()

    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def render(self, path, context=None):
        try:
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()

            # Если есть данные для подстановки
            if context:
                for key, value in context.items():
                    html = html.replace(key, value)

            self.send_html(html)
        except Exception as e:
            print(f"[RENDER ERROR] {e}")
            self.send_error(404)

    def serve_static(self):
        file_path = self.path.lstrip("/")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", self.mime_type(file_path))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404)

    def mime_type(self, path):
        ext = os.path.splitext(path)[1]
        return {".css": "text/css", ".js": "application/javascript", ".png": "image/png"}.get(ext,
                                                                                              "application/octet-stream")