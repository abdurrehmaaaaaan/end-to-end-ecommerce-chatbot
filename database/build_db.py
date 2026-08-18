"""
Loads products.json into a sqlite database using schema.sql.
Run this after the scraper has produced data/products.json.
"""

import json
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ecommerce.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
PRODUCTS_PATH = os.path.join(BASE_DIR, "data", "products.json")


def build_database():
    # fresh db each run
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(SCHEMA_PATH, "r") as f:
        cursor.executescript(f.read())

    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    insert_query = """
        INSERT OR IGNORE INTO products
        (name, brand, price, original_price, discount_percent,
         rating, review_count, url, cpu, ram_gb, storage, gpu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for p in products:
        cursor.execute(insert_query, (
            p.get("name"),
            p.get("brand"),
            p.get("price"),
            p.get("original_price"),
            p.get("discount_percent"),
            p.get("rating"),
            p.get("review_count"),
            p.get("url"),
            p.get("cpu"),
            p.get("ram_gb"),
            p.get("storage"),
            p.get("gpu"),
        ))

    conn.commit()

    count = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    print(f"loaded {count} products into {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    build_database()
