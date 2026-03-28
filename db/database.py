import psycopg2

def get_db():
    conn = psycopg2.connect(
        "dbname=kozlov user=postgres password=12345678 host=localhost port=5432"
    )
    return conn