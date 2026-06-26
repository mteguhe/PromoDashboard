import os
import sqlite3

def init_database(db_path="promo.db"):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")
