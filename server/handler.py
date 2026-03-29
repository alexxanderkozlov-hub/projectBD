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
        elif path == "/buy":
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

        elif path == "/change_key_status":
            k_id = query.get("id", [None])[0]
            status = query.get("status", [None])[0]
            if k_id and status:
                from models.key_model import update_key_status
                update_key_status(k_id, status)
            return self.redirect("/keys")

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
        # Получаем данные из тела запроса
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = urllib.parse.parse_qs(body)

        path = self.path
        print(f"--- POST запрос: {path} ---")

        # --- 1. АВТОРИЗАЦИЯ И ВЕРИФИКАЦИЯ (БЕЗ ПРОВЕРКИ СЕССИИ) ---
        if path == "/login":
            from routes.auth_routes import login
            return login(self, data)



        elif path == "/verify":
            from routes.auth_routes import verify
            return verify(self, data)
        # --- 2. ВСЕ ОСТАЛЬНЫЕ ДЕЙСТВИЯ (ТРЕБУЮТ АВТОРИЗАЦИИ И ПРОЙДЕННОГО 2FA) ---
        session = self.get_session()
        if not session or not session.get("2fa"):
            print(f"[POST] Доступ запрещен: сессия не авторизована для {path}")
            return self.redirect("/")

        # Далее пойдут твои остальные роуты (buy, add_product и т.д.)

        # ЛОГИКА ПОКУПКИ (для обычного юзера)
        if path == "/buy":
            lic_id = data.get("license_id", [None])[0]
            if lic_id:
                self.handle_purchase_logic(lic_id)
            else:
                self.send_error(400, "ID лицензии не указан")

        # ДОБАВЛЕНИЕ НОВОГО ПРОДУКТА (Admin Only)
        elif path == "/add_product":
            name = data.get("name", [""])[0]
            version = data.get("version", [""])[0]
            price = data.get("price", [""])[0]
            if name and version and price:
                from models.product_model import add_product
                add_product(name, version, price)
            self.redirect("/products")

        # ДОБАВЛЕНИЕ НОВОЙ ЛИЦЕНЗИИ (Admin Only)
        elif path == "/add_license":
            prod_id = data.get("product_id", [""])[0]
            l_type = data.get("license_type", [""])[0]
            dur = data.get("duration_days", [""])[0]
            if prod_id and l_type and dur:
                from models.license_model import add_license
                add_license(prod_id, l_type, dur)
            self.redirect("/licenses")

        # ДОБАВЛЕНИЕ КЛЮЧА ВРУЧНУЮ (Admin Only)
        elif path == "/add_key":
            lic_id = data.get("license_id", [""])[0]
            key_code = data.get("license_key", [""])[0]
            if lic_id and key_code:
                from models.key_model import add_new_key
                add_new_key(lic_id, key_code)
            self.redirect("/keys")

        else:
            self.send_error(404, "POST путь не найден")

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