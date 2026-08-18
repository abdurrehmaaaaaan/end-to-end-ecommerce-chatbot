import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os

BASE_URL = "https://priceoye.pk/laptops"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
MAX_PAGES = 6
DELAY_SECONDS = 2


def get_page(page_num):
    # fetch listing page
    url = BASE_URL if page_num == 1 else f"{BASE_URL}?page={page_num}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_cards(html):
    # find product cards
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("a[href*='/laptops/']")
    products = []
    seen_urls = set()

    for card in cards:
        href = card.get("href", "")
        if not href or href.rstrip("/") == BASE_URL:
            continue
        if href.count("/") < 4:
            continue
        full_url = href if href.startswith("http") else "https://priceoye.pk" + href
        if full_url in seen_urls:
            continue

        text = card.get_text(separator="|", strip=True)
        if not text or "Rs" not in text:
            continue

        seen_urls.add(full_url)
        products.append({"url": full_url, "raw_text": text})

    return products


def parse_price(raw_text):
    # extract price fields
    clean_text = raw_text.replace("|", " ")
    prices = re.findall(r"Rs\s?([\d,]+)", clean_text)
    prices = [int(p.replace(",", "")) for p in prices]

    if len(prices) >= 2:
        current_price, original_price = prices[0], prices[1]
    elif len(prices) == 1:
        current_price, original_price = prices[0], prices[0]
    else:
        current_price, original_price = None, None

    discount_pct = None
    disc_match = re.search(r"(\d+)%\s?OFF", clean_text)
    if disc_match:
        discount_pct = int(disc_match.group(1))

    return current_price, original_price, discount_pct


def parse_rating(raw_text):
    # extract rating and reviews
    clean_text = raw_text.replace("|", " ")
    rating, reviews = None, None
    rating_match = re.search(r"Rating Star\s?(\d)\s?(\d+)\s?Reviews?", clean_text)
    if rating_match:
        rating = int(rating_match.group(1))
        reviews = int(rating_match.group(2))
    return rating, reviews


def parse_name(raw_text):
    # extract product name
    parts = raw_text.split("|")
    for part in parts:
        if "Rs" not in part and "OFF" not in part and "Rating" not in part \
                and "Reviews" not in part and "Badge" not in part:
            if len(part) > 5:
                return part.strip()
    return parts[0].strip()


def extract_brand(name, url):
    # extract brand name
    match = re.search(r"/laptops/([a-zA-Z0-9-]+)/", url)
    if match:
        return match.group(1).upper()
    return name.split()[0].upper()


def extract_specs(name):
    # extract cpu ram storage
    cpu = None
    cpu_match = re.search(r"(Ci[3579]|Core i[3579]|Ultra [3579]|Ryzen [3579]|M[123]\s?Chip|N\d{3,4})[\w\-]*",
                           name, re.IGNORECASE)
    if cpu_match:
        cpu = cpu_match.group(0)

    ram = None
    ram_match = re.search(r"(\d{1,2})\s?GB\s?(RAM)?[-\s]", name, re.IGNORECASE)
    if ram_match:
        ram = ram_match.group(1) + "GB"

    storage = None
    storage_match = re.search(r"(\d{2,4})\s?GB\s?SSD", name, re.IGNORECASE)
    if not storage_match:
        storage_match = re.search(r"(\d)\s?TB\s?SSD", name, re.IGNORECASE)
        if storage_match:
            storage = storage_match.group(1) + "TB SSD"
    else:
        storage = storage_match.group(1) + "GB SSD"

    return cpu, ram, storage


def build_product_record(raw_card):
    url = raw_card["url"]
    raw_text = raw_card["raw_text"]

    name = parse_name(raw_text)
    price, original_price, discount_pct = parse_price(raw_text)
    rating, reviews = parse_rating(raw_text)
    brand = extract_brand(name, url)
    cpu, ram, storage = extract_specs(name)
    in_stock = "out of stock" not in raw_text.lower()

    return {
        "name": name,
        "brand": brand,
        "cpu": cpu,
        "ram": ram,
        "storage": storage,
        "price": price,
        "original_price": original_price,
        "discount_pct": discount_pct,
        "rating": rating,
        "review_count": reviews,
        "in_stock": in_stock,
        "url": url,
    }


def scrape_all_pages():
    # scrape all pages
    all_products = []
    seen_urls = set()

    for page in range(1, MAX_PAGES + 1):
        print(f"scraping page {page}")
        html = get_page(page)
        cards = extract_cards(html)

        if not cards:
            break

        for card in cards:
            if card["url"] in seen_urls:
                continue
            seen_urls.add(card["url"])
            record = build_product_record(card)
            if record["price"]:
                all_products.append(record)

        time.sleep(DELAY_SECONDS)

    return all_products


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "data", "products.json")

if __name__ == "__main__":
    products = scrape_all_pages()
    print(f"total products {len(products)}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    print(f"saved {OUTPUT_PATH}")
