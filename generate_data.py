"""
Synthetic retail data generator.
Produces realistic CSVs with intentional data quality issues.
Usage: python generate_data.py
Output: landing/{customers,products,stores,orders,order_items}.csv
"""
import csv
import random
import os
from datetime import date, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "landing")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def rand_date(start: date, end: date) -> str:
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()

def maybe_null(value, pct: float = 0.04):
    """Return None ~pct% of the time to simulate missing data."""
    return None if random.random() < pct else value

FIRST_NAMES = [
    "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Hank",
    "Iris", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Paul",
    "Quinn", "Rosa", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zoe", "Aaron", "Bella", "Carlos", "Diana",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
]
CITIES = [
    ("New York", "US"), ("Los Angeles", "US"), ("Chicago", "US"),
    ("Houston", "US"), ("Phoenix", "US"), ("Philadelphia", "US"),
    ("San Antonio", "US"), ("San Diego", "US"), ("Dallas", "US"),
    ("London", "GB"), ("Manchester", "GB"), ("Birmingham", "GB"),
    ("Toronto", "CA"), ("Vancouver", "CA"), ("Montreal", "CA"),
    ("Sydney", "AU"), ("Melbourne", "AU"), ("Brisbane", "AU"),
]
DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]

CATEGORIES = {
    "Electronics": ["Laptop", "Smartphone", "Tablet", "Headphones", "Smart Watch",
                    "Camera", "Monitor", "Keyboard", "Mouse", "USB Hub"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress",
                 "Hoodie", "Shorts", "Boots", "Socks", "Cap"],
    "Home & Garden": ["Coffee Maker", "Blender", "Vacuum Cleaner", "Lamp",
                      "Cushion", "Curtains", "Plant Pot", "Rug", "Mirror", "Clock"],
    "Sports": ["Yoga Mat", "Dumbbells", "Running Shoes", "Bicycle Helmet",
               "Water Bottle", "Resistance Bands", "Jump Rope", "Tennis Racket",
               "Basketball", "Swim Goggles"],
    "Books": ["Fiction Novel", "Business Guide", "Cookbook", "Self-Help Book",
              "History Book", "Science Textbook", "Art Book", "Travel Guide",
              "Children Story", "Poetry Collection"],
}
SUB_CATEGORIES = {
    "Electronics": ["Computing", "Mobile", "Audio", "Wearables", "Photography", "Accessories"],
    "Clothing": ["Tops", "Bottoms", "Outerwear", "Footwear", "Accessories"],
    "Home & Garden": ["Kitchen", "Living Room", "Bedroom", "Garden", "Decor"],
    "Sports": ["Fitness", "Outdoor", "Team Sports", "Water Sports", "Cycling"],
    "Books": ["Fiction", "Non-Fiction", "Educational", "Children", "Reference"],
}

REGIONS = ["North", "South", "East", "West", "Central"]
STORE_CITIES = [
    ("New York", "US"), ("Los Angeles", "US"), ("Chicago", "US"),
    ("Houston", "US"), ("London", "GB"), ("Toronto", "CA"),
    ("Sydney", "AU"), ("Dallas", "US"), ("Miami", "US"),
    ("Seattle", "US"), ("Boston", "US"), ("Atlanta", "US"),
    ("Denver", "US"), ("Phoenix", "US"), ("Manchester", "GB"),
    ("Birmingham", "GB"), ("Vancouver", "CA"), ("Melbourne", "AU"),
    ("Brisbane", "AU"), ("Montreal", "CA"),
]

STATUSES = ["completed", "completed", "completed", "completed",  # weighted toward completed
            "returned", "cancelled", "pending"]


# ── customers (~500) ─────────────────────────────────────────────────────────

def generate_customers(n: int = 500):
    rows = []
    used_emails = set()
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city, country = random.choice(CITIES)

        # Data quality: ~2% have garbled email format, ~4% have null email
        raw_email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{random.choice(DOMAINS)}"
        if random.random() < 0.02:
            raw_email = raw_email.replace("@", "AT")   # bad format
        if raw_email in used_emails and random.random() < 0.01:
            raw_email = raw_email  # intentional duplicate email for ~1%
        used_emails.add(raw_email)

        signup = rand_date(date(2018, 1, 1), date(2024, 6, 30))

        rows.append({
            "customer_id": i,
            "name": f"{first} {last}",
            "email": maybe_null(raw_email, 0.03),
            "city": maybe_null(city, 0.02),
            "country": country,
            "signup_date": signup,
        })

    # Inject 5 duplicate rows (same customer_id re-submitted)
    for _ in range(5):
        rows.append(random.choice(rows[:n]).copy())

    return rows


# ── products (~100) ──────────────────────────────────────────────────────────

def generate_products(n: int = 100):
    rows = []
    pid = 1
    for cat, items in CATEGORIES.items():
        sub_cats = SUB_CATEGORIES[cat]
        for item in items:
            cost = round(random.uniform(3, 400), 2)
            margin = random.uniform(0.25, 1.20)
            price = round(cost * (1 + margin), 2)

            # Data quality: ~3% have negative unit_cost (corrupt record)
            if random.random() < 0.03:
                cost = -cost

            rows.append({
                "product_id": pid,
                "name": item,
                "category": cat,
                "sub_category": random.choice(sub_cats),
                "unit_cost": cost,
                "unit_price": price,
            })
            pid += 1

    # Pad to n if needed
    while len(rows) < n:
        cat = random.choice(list(CATEGORIES.keys()))
        items = CATEGORIES[cat]
        sub_cats = SUB_CATEGORIES[cat]
        cost = round(random.uniform(3, 400), 2)
        rows.append({
            "product_id": pid,
            "name": random.choice(items) + " Pro",
            "category": cat,
            "sub_category": random.choice(sub_cats),
            "unit_cost": cost,
            "unit_price": round(cost * random.uniform(1.25, 2.20), 2),
        })
        pid += 1

    return rows[:n]


# ── stores (~20) ─────────────────────────────────────────────────────────────

def generate_stores():
    rows = []
    for i, (city, country) in enumerate(STORE_CITIES, start=1):
        region = random.choice(REGIONS)
        opened = rand_date(date(2010, 1, 1), date(2022, 12, 31))
        rows.append({
            "store_id": i,
            "name": f"{city} Store",
            "region": region,
            "country": country,
            "opened_date": opened,
        })
    return rows


# ── orders (~5 000) ──────────────────────────────────────────────────────────

def generate_orders(n: int = 5000, n_customers: int = 500, n_stores: int = 20):
    rows = []
    for i in range(1, n + 1):
        order_date = rand_date(date(2022, 1, 1), date(2024, 12, 31))

        # Data quality: ~1% have NULL customer_id
        cust = maybe_null(random.randint(1, n_customers), 0.01)
        store = random.randint(1, n_stores)
        status = random.choice(STATUSES)

        rows.append({
            "order_id": i,
            "customer_id": cust,
            "store_id": store,
            "order_date": order_date,
            "status": status,
        })
    return rows


# ── order_items (~15 000) ─────────────────────────────────────────────────────

def generate_order_items(orders, n_products: int = 100):
    rows = []
    for order in orders:
        oid = order["order_id"]
        # 1–6 line items per order  (weights give E[X]≈3.2 → ~16k items across 5k orders)
        n_lines = random.choices([1, 2, 3, 4, 5, 6], weights=[8, 17, 28, 24, 15, 8])[0]
        chosen_products = random.sample(range(1, n_products + 1), min(n_lines, n_products))
        for pid in chosen_products:
            qty = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            discount = random.choices(
                [0.0, 0.05, 0.10, 0.15, 0.20, 0.25],
                weights=[50, 15, 15, 10, 7, 3]
            )[0]

            # Data quality: ~1% have quantity = 0 or negative
            if random.random() < 0.01:
                qty = random.choice([0, -1])

            rows.append({
                "order_id": oid,
                "product_id": pid,
                "quantity": qty,
                "discount_pct": discount,
            })
    return rows


# ── writer ────────────────────────────────────────────────────────────────────

def write_csv(filename: str, rows: list, fieldnames: list):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  wrote {len(rows):>6} rows → {path}")


if __name__ == "__main__":
    print("Generating synthetic retail data …")

    customers = generate_customers(500)
    products = generate_products(100)
    stores = generate_stores()
    orders = generate_orders(5000)
    order_items = generate_order_items(orders, n_products=100)

    write_csv("customers.csv", customers,
              ["customer_id", "name", "email", "city", "country", "signup_date"])
    write_csv("products.csv", products,
              ["product_id", "name", "category", "sub_category", "unit_cost", "unit_price"])
    write_csv("stores.csv", stores,
              ["store_id", "name", "region", "country", "opened_date"])
    write_csv("orders.csv", orders,
              ["order_id", "customer_id", "store_id", "order_date", "status"])
    write_csv("order_items.csv", order_items,
              ["order_id", "product_id", "quantity", "discount_pct"])

    print("Done.")
