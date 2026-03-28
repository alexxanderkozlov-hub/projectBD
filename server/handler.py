from http.server import BaseHTTPRequestHandler
import urllib.parse
import os

from routes.auth_routes import login, verify
from routes.dashboard_routes import dashboard


class MyHandler(BaseHTTPRequestHandler):
    # ================= ГЛОБАЛЬНОЕ СОСТОЯНИЕ =================
    # Используем словари на уровне класса для хранения данных между запросами
    sessions = {}  # session_id -> {"user": user_dict, "2fa": bool}
    codes = {}  # session_id -> 2FA code

    # ================= GET =================
    def do_GET(self):
        # Парсим путь, чтобы отделить сам адрес от параметров (?tab=products)
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(f"GET запрос: {path}")

        if path == "/":
            self.render("templates/login.html")

        elif path == "/2fa":
            # Проверяем, есть ли вообще сессия, прежде чем пускать на ввод кода
            if not self.get_session():
                self.redirect("/")
                return
            self.render("templates/2fa.html")

        elif path == "/dashboard":
            session = self.get_session()
            # 1. Нет сессии — на логин
            if not session:
                self.redirect("/")
                return
            # 2. Сессия есть, но 2FA еще False — на ввод кода
            if not session.get("2fa"):
                self.redirect("/2fa")
                return
            # 3. Всё успешно — вызываем логику дашборда
            dashboard(self)

        # --- НОВЫЙ БЛОК: СТРАНИЦА ПРОДУКТОВ ---
        elif path == "/products":
            session = self.get_session()
            # Проверка: залогинен ли пользователь и прошел ли он 2FA
            if not session or not session.get("2fa"):
                print("Доступ к продуктам запрещен: нет авторизации")
                self.redirect("/")
                return

            # Импортируем функцию отрисовки (если она в другом файле)
            from routes.dashboard_routes import show_products
            show_products(self)
        # --------------------------------------

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

        if self.path == "/login":
            login(self, data)

        elif self.path == "/verify":
            verify(self, data)

        else:
            self.send_error(404, "Not Found")

    # ================= SESSION MANAGEMENT =================
    def get_session(self):
        """Извлекает сессию из куки session_id"""
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None

        # Парсим куки в словарь
        cookies = {}
        for entry in cookie_header.split(";"):
            if "=" in entry:
                key, val = entry.strip().split("=", 1)
                cookies[key] = val

        session_id = cookies.get("session_id")
        if not session_id:
            return None

        # Обращаемся к словарю через класс, чтобы данные были видны всем запросам
        return MyHandler.sessions.get(session_id)

    def get_user(self):
        """Возвращает данные пользователя из текущей сессии"""
        session = self.get_session()
        if session:
            return session.get("user")
        return None

    # ================= ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =================
    def serve_static(self):
        # Убираем начальный слэш и проверяем существование файла
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
        except Exception as e:
            print(f"Ошибка статики: {e}")
            self.send_error(500)

    def mime_type(self, path):
        if path.endswith(".css"): return "text/css"
        if path.endswith(".js"): return "application/javascript"
        if path.endswith(".png"): return "image/png"
        if path.endswith(".jpg") or path.endswith(".jpeg"): return "image/jpeg"
        return "application/octet-stream"

    def render(self, path):
        """Загружает HTML шаблон и отправляет его клиенту"""
        if not os.path.exists(path):
            self.send_error(404, f"Шаблон {path} не найден")
            return

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def redirect(self, path):
        """Выполняет HTTP редирект"""
        self.send_response(302)
        self.send_header("Location", path)
        self.end_headers()