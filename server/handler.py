from http.server import BaseHTTPRequestHandler
import urllib.parse
import os

from routes.auth_routes import login, verify
from routes.dashboard_routes import dashboard


class MyHandler(BaseHTTPRequestHandler):
    # ================= ГЛОБАЛЬНОЕ СОСТОЯНИЕ =================
    sessions = {}  # session_id -> {"user": user_dict, "2fa": bool}
    codes = {}     # session_id -> 2FA code

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

        # 4. Список продуктов
        elif path == "/products":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            from routes.dashboard_routes import show_products
            show_products(self)

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

        # 6. Страница добавления (Отображение пустой формы)
        elif path == "/add_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return
            self.render("templates/add_product.html")

        # 7. Страница редактирования (Отображение формы с данными)
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

                    html = html.replace("{{ID}}", str(p[0]))
                    html = html.replace("{{NAME}}", str(p[1]))
                    html = html.replace("{{VERSION}}", str(p[2]))
                    html = html.replace("{{PRICE}}", str(p[3]))

                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                    return

            self.redirect("/products")

        # 8. Статика
        elif path.startswith("/static/"):
            self.serve_static()

        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()

        else:
            self.send_error(404, "Страница не найдена")

    # ================= POST =================
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        data = urllib.parse.parse_qs(body)

        print(f"POST запрос: {self.path}")

        # Авторизация
        if self.path == "/login":
            login(self, data)
        elif self.path == "/verify":
            verify(self, data)

        # Обработка добавления нового продукта
        elif self.path == "/add_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return

            name = data.get("name", [None])[0]
            version = data.get("version", [None])[0]
            price = data.get("price", [None])[0]

            if name and version and price:
                from models.product_model import add_product
                add_product(name, version, price)

            self.redirect("/products")

        # Обработка сохранения изменений продукта
        elif self.path == "/edit_product":
            session = self.get_session()
            if not session or not session.get("2fa"):
                self.redirect("/")
                return

            p_id = data.get("product_id", [None])[0]
            name = data.get("name", [None])[0]
            version = data.get("version", [None])[0]
            price = data.get("price", [None])[0]

            if p_id and name and version and price:
                from models.product_model import update_product
                update_product(p_id, name, version, price)

            self.redirect("/products")

        else:
            self.send_error(404, "Not Found")

    # ================= ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (Остаются без изменений) =================
    def get_session(self):
        cookie_header = self.headers.get("Cookie")
        if not cookie_header: return None
        cookies = {}
        for entry in cookie_header.split(";"):
            if "=" in entry:
                key, val = entry.strip().split("=", 1)
                cookies[key] = val
        session_id = cookies.get("session_id")
        return MyHandler.sessions.get(session_id)

    def get_user(self):
        session = self.get_session()
        return session.get("user") if session else None

    def serve_static(self):
        file_path = self.path.lstrip("/")
        if not os.path.exists(file_path):
            self.send_error(404)
            return
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", self.mime_type(file_path))
            self.end_headers()
            self.wfile.write(content)
        except: self.send_error(500)

    def mime_type(self, path):
        if path.endswith(".css"): return "text/css"
        if path.endswith(".js"): return "application/javascript"
        if path.endswith(".png"): return "image/png"
        if path.endswith(".jpg"): return "image/jpeg"
        return "application/octet-stream"

    def render(self, path):
        if not os.path.exists(path):
            self.send_error(404)
            return
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