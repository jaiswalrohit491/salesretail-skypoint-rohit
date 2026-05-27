"""
CSV → PostgreSQL raw schema loader.
Reads every CSV from /landing and bulk-loads it into the `raw` schema.
Tables are dropped and recreated on each run (full-refresh landing load).
"""
import csv
import io
import logging
import os
import sys
import time

import psycopg2
from psycopg2 import sql

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [loader] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── config ────────────────────────────────────────────────────────────────────

DB_HOST    = os.environ.get("DB_HOST", "db")
DB_PORT    = int(os.environ.get("DB_PORT", 5432))
DB_NAME    = os.environ.get("DB_NAME", "retail")
DB_USER    = os.environ.get("DB_USER", "retail")
DB_PASS    = os.environ.get("DB_PASS", "retail_pass")
DB_SSLMODE = os.environ.get("DB_SSLMODE", "prefer")
LANDING_DIR = os.environ.get("LANDING_DIR", "/landing")
RAW_SCHEMA = "raw"

# Explicit column type hints (everything else lands as TEXT then DBT casts it)
COLUMN_TYPES: dict[str, dict[str, str]] = {
    "customers":   {"customer_id": "INTEGER"},
    "products":    {"product_id": "INTEGER", "unit_cost": "NUMERIC", "unit_price": "NUMERIC"},
    "stores":      {"store_id": "INTEGER"},
    "orders":      {"order_id": "INTEGER", "customer_id": "INTEGER", "store_id": "INTEGER"},
    "order_items": {"order_id": "INTEGER", "product_id": "INTEGER",
                    "quantity": "INTEGER", "discount_pct": "NUMERIC"},
}


# ── helpers ───────────────────────────────────────────────────────────────────

def wait_for_db(max_attempts: int = 30, delay: float = 2.0) -> psycopg2.extensions.connection:
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                sslmode=DB_SSLMODE,
            )
            log.info("Connected to PostgreSQL on attempt %d", attempt)
            return conn
        except psycopg2.OperationalError as exc:
            log.warning("DB not ready (attempt %d/%d): %s", attempt, max_attempts, exc)
            time.sleep(delay)
    log.error("Could not connect to DB after %d attempts – aborting.", max_attempts)
    sys.exit(1)


def col_ddl(name: str, table: str) -> str:
    types = COLUMN_TYPES.get(table, {})
    return f"{sql.Identifier(name).as_string(None)} {types.get(name, 'TEXT')}"


def load_csv(conn, csv_path: str) -> None:
    table_name = os.path.splitext(os.path.basename(csv_path))[0]
    log.info("Loading %s …", csv_path)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            log.warning("  %s is empty – skipping", csv_path)
            return
        columns = reader.fieldnames

    # Build column DDL
    col_defs = ", ".join(
        f"{psycopg2.extensions.quote_ident(c, conn)} "
        f"{COLUMN_TYPES.get(table_name, {}).get(c, 'TEXT')}"
        for c in columns
    )
    full_table = f"{RAW_SCHEMA}.{table_name}"

    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {full_table} CASCADE")
        cur.execute(f"CREATE TABLE {full_table} ({col_defs})")

        # Stream via COPY for efficiency; handle NULLs represented as empty string
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        buf.seek(0)

        cur.copy_expert(
            f"COPY {full_table} ({', '.join(psycopg2.extensions.quote_ident(c, conn) for c in columns)}) "
            f"FROM STDIN WITH CSV HEADER NULL ''",
            buf,
        )

    conn.commit()
    log.info("  → %d rows loaded into %s", len(rows), full_table)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    conn = wait_for_db()

    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {RAW_SCHEMA}")
    conn.commit()
    log.info("Schema '%s' ready", RAW_SCHEMA)

    csv_files = sorted(
        os.path.join(LANDING_DIR, f)
        for f in os.listdir(LANDING_DIR)
        if f.endswith(".csv")
    )
    if not csv_files:
        log.error("No CSV files found in %s", LANDING_DIR)
        sys.exit(1)

    for path in csv_files:
        load_csv(conn, path)

    conn.close()
    log.info("All files loaded successfully.")


if __name__ == "__main__":
    main()
