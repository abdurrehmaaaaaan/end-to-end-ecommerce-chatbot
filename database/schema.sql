-- products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand TEXT,
    price INTEGER,
    original_price INTEGER,
    discount_percent REAL,
    rating REAL,
    review_count INTEGER,
    url TEXT UNIQUE,
    cpu TEXT,
    ram_gb INTEGER,
    storage TEXT,
    gpu TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_ram ON products(ram_gb);
