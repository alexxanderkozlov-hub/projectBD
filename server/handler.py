from http.server import BaseHTTPRequestHandler
import urllib.parse
import os

from routes.auth_routes import login, verify
from routes.dashboard_routes import dashboard


class MyHandler(BaseHTTPRequestHandler):
    # ================= ГЛОБАЛЬНОЕ СОСТОЯНИЕ =================
    sessions = {}  # session_id -> {"user": user_dict, "2fa": bool}
    codes = {}  # session_id -> 2FA code

    # ================= GET =================
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(f"GET запрос: {path}")

        # 1. Главная страница (Логин)
        if path == "/":
            self.render("templates/login.html")

        # 2. Двухфакторная аутентификация
        elif path == "/2fa":
            if not self.get_session():
                self.redirect("/")
                return
            self.render("templates/2fa.html")

        # 3. Главная панель (Дашборд)
        elif path == "/dashboard":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            dashboard(self)

        # 4. Продукты (Список)
        elif path == "/products":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            from routes.dashboard_routes import show_products
            show_products(self)

        # 4.1 Лицензии (Список)
        elif path == "/licenses":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            from routes.dashboard_routes import show_licenses
            show_licenses(self)

        # 5. Удаление продукта
        elif path == "/delete_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            query = urllib.parse.parse_qs(parsed_path.query)
            product_id = query.get("id", [None])[0]
            if product_id:
                from models.product_model import delete_product_by_id
                delete_product_by_id(product_id)
            self.redirect("/products")

        # 5.1 Удаление лицензии
        elif path == "/delete_license":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            query = urllib.parse.parse_qs(parsed_path.query)
            lic_id = query.get("id", [None])[0]
            if lic_id:
                from models.license_model import delete_license_by_id
                delete_license_by_id(lic_id)
            self.redirect("/licenses")

        # 6. Добавление продукта (Страница)
        elif path == "/add_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            self.render("templates/add_product.html")

        # 6.1 Выдача лицензии (Страница с формой)
        elif path == "/add_license":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return

            from models.product_model import get_all_products
            products = get_all_products()

            # Читаем шаблон формы выдачи лицензии
            with open("templates/add_license.html", "r", encoding="utf-8") as f:
                html = f.read()

            # Генерируем выпадающий список из реальных продуктов в БД
            options = ""
            for p in products:
                options += f'<option value="{p[0]}">{p[1]} (v.{p[2]})</option>'

            html = html.replace("{{PRODUCT_OPTIONS}}", options)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        # 7. Редактирование продукта
        elif path == "/edit_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            query = urllib.parse.parse_qs(parsed_path.query)
            product_id = query.get("id", [None])[0]
            if product_id:
                from models.product_model import get_product_by_id
                p = get_product_by_id(product_id)
                if p:
                    with open("templates/edit_product.html", "r", encoding="utf-8") as f:
                        html = f.read()
                    html = html.replace("{{ID}}", str(p[0])).replace("{{NAME}}", str(p[1]))
                    html = html.replace("{{VERSION}}", str(p[2])).replace("{{PRICE}}", str(p[3]))
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                    return
            self.redirect("/products")

        # 7.1 Редактирование лицензии
        elif path == "/edit_license":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            query = urllib.parse.parse_qs(parsed_path.query)
            lic_id = query.get("id", [None])[0]
            if lic_id:
                from models.license_model import get_license_by_id
                from models.product_model import get_all_products
                lic = get_license_by_id(lic_id)
                products = get_all_products()
                if lic:
                    with open("templates/edit_license.html", "r", encoding="utf-8") as f:
                        html = f.read()

                    options = ""
                    for p in products:
                        selected = "selected" if p[0] == lic[1] else ""
                        options += f'<option value="{p[0]}" {selected}>{p[1]}</option>'

                    html = html.replace("{{ID}}", str(lic[0]))
                    html = html.replace("{{PRODUCT_OPTIONS}}", options)
                    html = html.replace("{{DURATION}}", str(lic[3]))
                    html = html.replace(f'value="{lic[2]}"', f'value="{lic[2]}" selected')

                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                    return
            self.redirect("/licenses")

        # 8. Статика
        elif path.startswith("/static/"):
            self.serve_static()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404, "Page not found")

    # ================= POST =================
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        data = urllib.parse.parse_qs(body)

        print(f"POST запрос: {self.path}")

        if self.path == "/login":
            login(self, data)
        elif self.path == "/verify":
            verify(self, data)

        # POST: Добавление продукта
        elif self.path == "/add_product":
            name = data.get("name", [""])[0]
            ver = data.get("version", [""])[0]
            price = data.get("price", [""])[0]
            if name and ver and price:
                from models.product_model import add_product
                add_product(name, ver, price)
            self.redirect("/products")

        # POST: Выдача новой лицензии (Сохранение)
        elif self.path == "/add_license":
            prod_id = data.get("product_id", [""])[0]
            l_type = data.get("license_type", [""])[0]
            dur = data.get("duration_days", [""])[0]
            if prod_id and l_type and dur:
                from models.license_model import add_license
                add_license(prod_id, l_type, dur)
            self.redirect("/licenses")

        # POST: Изменение продукта
        elif self.path == "/edit_product":
            p_id = data.get("product_id", [""])[0]
            name = data.get("name", [""])[0]
            ver = data.get("version", [""])[0]
            price = data.get("price", [""])[0]
            if p_id and name and ver and price:
                from models.product_model import update_product
                update_product(p_id, name, ver, price)
            self.redirect("/products")

        # POST: Изменение лицензии
        elif self.path == "/edit_license":
            lic_id = data.get("license_id", [""])[0]
            prod_id = data.get("product_id", [""])[0]
            l_type = data.get("license_type", [""])[0]
            dur = data.get("duration_days", [""])[0]
            if lic_id and prod_id and l_type and dur:
                from models.license_model import update_license
                update_license(lic_id, prod_id, l_type, dur)
            self.redirect("/licenses")

        else:
            self.send_error(404, "Not Found")

    # ================= ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =================
    def get_session(self):
        cookie_header = self.headers.get("Cookie")
        if not cookie_header: return None
        cookies = {k.strip(): v for k, v in (e.split("=", 1) for e in cookie_header.split(";") if "=" in e)}
        return MyHandler.sessions.get(cookies.get("session_id"))

    def get_user(self):
        session = self.get_session()
        return session.get("user") if session else None

    def serve_static(self):
        file_path = self.path.lstrip("/")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", self.mime_type(file_path))
            self.end_headers()
            self.wfile.write(content)

    def mime_type(self, path):
        types = {".css": "text/css", ".js": "application/javascript", ".png": "image/png", ".jpg": "image/jpeg"}
        return types.get(os.path.splitext(path)[1], "application/octet-stream")

    def render(self, path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def redirect(self, path):
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()