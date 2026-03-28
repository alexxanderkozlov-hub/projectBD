from db.database import get_db


def get_all_products():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT product_id, name, version, price
        FROM products
        ORDER BY product_id DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def create_product(name, version, price):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO products (name, version, price)
        VALUES (%s, %s, %s)
    """, (name, version, price))

    conn.commit()
    cur.close()
    conn.close()