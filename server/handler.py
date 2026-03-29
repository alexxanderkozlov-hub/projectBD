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

        print(f"GET запрос: {path}")

        # 1. Публичные роуты и статика
        if path == "/":
            return self.render("templates/login.html")

        if path.startswith("/static/"):
            return self.serve_static()

        if path == "/favicon.ico":
            self.send_response(204)
            return self.end_headers()

        # 2. Проверка сессии для 2FA
        if path == "/2fa":
            if not self.get_session():
                return self.redirect("/")
            return self.render("templates/2fa.html")

        # 3. Закрытая зона (Требует авторизации и 2FA)
        session = self.get_session()
        if not session or not session.get("2fa"):
            return self.redirect("/")

        # --- КОРРЕКТНЫЕ РОУТЫ ---

        if path == "/dashboard":
            dashboard(self)

        elif path == "/products":
            show_products(self)

        elif path == "/licenses":
            show_licenses(self)

        elif path == "/keys":
            show_keys(self)

        # ВОТ ЭТОГО БЛОКА ТЕБЕ НЕ ХВАТАЛО (для лога GET /orders)
        elif path == "/orders":
            show_buy_page(self)

        # Обработка нажатия на кнопку "Купить" (через ссылку)
        elif path == "/buy":
            lic_id = query.get("license_id", [None])[0]
            self.handle_purchase_logic(lic_id)

        # ===== УДАЛЕНИЕ =====
        elif path == "/delete_product":
            p_id = query.get("id", [None])[0]
            if p_id:
                from models.product_model import delete_product_by_id
                delete_product_by_id(p_id)
            self.redirect("/products")

        elif path == "/delete_license":
            l_id = query.get("id", [None])[0]
            if l_id:
                from models.license_model import delete_license_by_id
                delete_license_by_id(l_id)
            self.redirect("/licenses")

        elif path == "/delete_key":
            k_id = query.get("id", [None])[0]
            if k_id:
                from models.key_model import delete_key_by_id
                delete_key_by_id(k_id)
            self.redirect("/keys")

        elif path == "/change_key_status":
            k_id = query.get("id", [None])[0]
            status = query.get("status", [None])[0]
            if k_id and status:
                from models.key_model import update_key_status
                update_key_status(k_id, status)
            self.redirect("/keys")

        # ===== ДОБАВЛЕНИЕ (Страницы) =====
        elif path == "/add_product":
            self.render("templates/add_product.html")

        elif path == "/add_license":
            # Используем твой код генерации списка продуктов
            from models.product_model import get_all_products
            products = get_all_products()
            with open("templates/add_license.html", "r", encoding="utf-8") as f:
                html = f.read()
            options = "".join([f'<option value="{p[0]}">{p[1]} (v.{p[2]})</option>' for p in products])
            self.send_html(html.replace("{{PRODUCT_OPTIONS}}", options))

        elif path == "/add_key":
            from models.license_model import get_all_licenses
            lics = get_all_licenses()
            with open("templates/add_key.html", "r", encoding="utf-8") as f:
                html = f.read()
            options = "".join([f'<option value="{l[0]}">{l[1]} ({l[2]}) - ID:{l[0]}</option>' for l in lics])
            self.send_html(html.replace("{{LICENSE_OPTIONS}}", options))

        else:
            self.send_error(404, f"Path {path} not found")

    def do_POST(self):
        # Получаем данные из тела запроса
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        data = urllib.parse.parse_qs(body)

        print(f"POST запрос: {self.path}")

        # --- 1. АВТОРИЗАЦИЯ И ВЕРИФИКАЦИЯ (БЕЗ ПРОВЕРКИ СЕССИИ) ---
        if self.path == "/login":
            return login(self, data)

        elif self.path == "/verify":
            return verify(self, data)

        # --- 2. ВСЕ ОСТАЛЬНЫЕ ДЕЙСТВИЯ (ТРЕБУЮТ АВТОРИЗАЦИИ) ---
        # Проверяем, залогинен ли пользователь, прежде чем что-то добавлять или покупать
        session = self.get_session()
        if not session or not session.get("2fa"):
            print("Попытка POST запроса без авторизации")
            return self.redirect("/")

        # Логика покупки
        if self.path == "/buy":
            lic_id = data.get("license_id", [None])[0]
            self.handle_purchase_logic(lic_id)

        # Добавление нового продукта (ПО)
        elif self.path == "/add_product":
            name = data.get("name", [""])[0]
            version = data.get("version", [""])[0]
            price = data.get("price", [""])[0]
            if name and version and price:
                from models.product_model import add_product
                add_product(name, version, price)
            self.redirect("/products")

        # Добавление новой лицензии
        elif self.path == "/add_license":
            prod_id = data.get("product_id", [""])[0]
            l_type = data.get("license_type", [""])[0]
            dur = data.get("duration_days", [""])[0]
            if prod_id and l_type and dur:
                from models.license_model import add_license
                add_license(prod_id, l_type, dur)
            self.redirect("/licenses")

        # Добавление ключа вручную
        elif self.path == "/add_key":
            lic_id = data.get("license_id", [""])[0]
            key_code = data.get("license_key", [""])[0]
            if lic_id and key_code:
                from models.key_model import add_new_key
                add_new_key(lic_id, key_code)
            self.redirect("/keys")

        else:
            self.send_error(404, "POST путь не найден")

    # Вспомогательный метод для покупки
    def handle_purchase_logic(self, lic_id):
        user = self.get_user()
        if not user or not lic_id:
            return self.send_error(400, "Ошибка: нет данных пользователя или ID лицензии")
        try:
            # Определяем ID пользователя (поддержка и словаря, и кортежа)
            user_id = user.get("id") if isinstance(user, dict) else user[0]

            from models.purchase_model import make_purchase
            if make_purchase(user_id, int(lic_id)):
                print(f"Успешная покупка: User {user_id}, Lic {lic_id}")
                self.redirect("/keys")
            else:
                self.send_error(500, "Ошибка БД при покупке")
        except Exception as e:
            print(f"Критическая ошибка покупки: {e}")
            self.send_error(500, str(e))

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

    def render(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.send_html(f.read())
        except:
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