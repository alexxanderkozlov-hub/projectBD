from db.database import get_db
from utils.hash import hash_password

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # =========================
    # CREATE TABLE
    # =========================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # =========================
    # CLEAN OLD DATA (чтобы не было конфликтов)
    # =========================
    cur.execute("DELETE FROM users")

    # =========================
    # INSERT USERS (bcrypt hashed)
    # =========================
    users = [
        ("admin", "admin123", "admin"),
        ("user", "user123", "user")
    ]

    for login, password, role in users:
        hashed_password = hash_password(password)

        cur.execute("""
        INSERT INTO users (login, password, role)
        VALUES (%s, %s, %s)
        """, (login, hashed_password, role))

    conn.commit()
    cur.close()
    conn.close()

    print("DB READY ✔ USERS CREATED")


if __name__ == "__main__":
    init_db()