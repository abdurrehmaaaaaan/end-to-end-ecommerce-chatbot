"""
Turns a natural language query into a filtered sql query against the
products table using keyword and regex based slot extraction. Not a
full nl2sql model, deliberately kept simple and explainable.
"""

import re
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "ecommerce.db")

KNOWN_BRANDS = ["hp", "dell", "lenovo", "acer", "apple", "asus", "infinix"]
CPU_KEYWORDS = {
    "i3": "i3", "core i3": "i3", "ci3": "i3",
    "i5": "i5", "core i5": "i5", "ci5": "i5",
    "i7": "i7", "core i7": "i7", "ci7": "i7",
    "i9": "i9", "core i9": "i9", "ci9": "i9",
    "ryzen": "ryzen", "ultra": "ultra",
}


def extract_filters(query):
    q = query.lower()
    filters = {}

    for brand in KNOWN_BRANDS:
        if brand in q:
            filters["brand"] = brand.upper()
            break

    price_range = re.search(r"between\s+(\d[\d,]*)\s*(?:and|to)\s+(\d[\d,]*)", q)
    if price_range:
        filters["min_price"] = int(price_range.group(1).replace(",", ""))
        filters["max_price"] = int(price_range.group(2).replace(",", ""))
    else:
        under_match = re.search(r"under\s+(\d[\d,]*)", q)
        if under_match:
            filters["max_price"] = int(under_match.group(1).replace(",", ""))
        above_match = re.search(r"(?:above|over)\s+(\d[\d,]*)", q)
        if above_match:
            filters["min_price"] = int(above_match.group(1).replace(",", ""))

    ram_match = re.search(r"(\d+)\s*gb", q)
    if ram_match:
        filters["ram_gb"] = int(ram_match.group(1))

    for keyword, cpu_tag in CPU_KEYWORDS.items():
        if keyword in q:
            filters["cpu_like"] = cpu_tag
            break

    if "cheapest" in q or "lowest price" in q:
        filters["sort"] = "price_asc"
    elif "most expensive" in q or "highest price" in q:
        filters["sort"] = "price_desc"

    if "gaming" in q or "rtx" in q or "gpu" in q or "graphics card" in q:
        filters["gpu_required"] = True

    return filters


def build_sql(filters, limit=5):
    where_clauses = []
    params = []

    if "brand" in filters:
        where_clauses.append("brand = ?")
        params.append(filters["brand"])
    if "min_price" in filters:
        where_clauses.append("price >= ?")
        params.append(filters["min_price"])
    if "max_price" in filters:
        where_clauses.append("price <= ?")
        params.append(filters["max_price"])
    if "ram_gb" in filters:
        where_clauses.append("ram_gb = ?")
        params.append(filters["ram_gb"])
    if "cpu_like" in filters:
        where_clauses.append("cpu LIKE ?")
        params.append(f"%{filters['cpu_like']}%")
    if filters.get("gpu_required"):
        where_clauses.append("gpu IS NOT NULL")

    query = "SELECT name, brand, price, cpu, ram_gb, storage, gpu, url FROM products"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    if filters.get("sort") == "price_asc":
        query += " ORDER BY price ASC"
    elif filters.get("sort") == "price_desc":
        query += " ORDER BY price DESC"
    else:
        query += " ORDER BY rating DESC"

    query += f" LIMIT {limit}"
    return query, params


def run_sql_query(user_query, limit=5):
    filters = extract_filters(user_query)
    sql, params = build_sql(filters, limit)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "filters": filters,
        "sql": sql,
        "params": params,
        "results": rows,
    }
