# Retail Sales Analytics Pipeline

An end-to-end data pipeline that ingests raw CSV exports from a retail landing zone,
transforms them into a clean star-schema dimensional model using DBT, and surfaces
insights through a Power BI semantic model and report.

---

## a) Project Overview

The pipeline answers the following business questions:

| Question | Answered by |
|---|---|
| Total sales by store, category, and month | `fact_sales` joined to `dim_store`, `dim_product`, `dim_date` |
| Top 10 customers by revenue | `fact_sales` aggregated on `customer_sk` |
| Products with highest / lowest gross margin | `dim_product.gross_margin_pct` |
| Sales performance trend over time | `fact_sales` × `dim_date` (monthly / quarterly grain) |

---

## b) Architecture

```
landing/          raw CSVs (customers, products, stores, orders, order_items)
    │
    │  Docker Compose
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  service: db  (PostgreSQL 16 — local Docker, default)               │
│    OR  Neon cloud PostgreSQL (optional override via .env)           │
│                                                                     │
│    schema raw      ← populated by loader                            │
│    schema staging  ← DBT views                                      │
│    schema marts    ← DBT tables (star schema)                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       service: loader             service: dbt
       (Python, psycopg2)          (dbt-postgres 1.8.2)
       Reads CSVs → raw            staging → marts
       schema via COPY             runs 40 tests
              │                         │
              └────────────┬────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     Power BI Desktop            Power BI Service
     (Windows)                   (macOS / browser)
     localhost:5432               Neon cloud DB
```

### Data quality issues handled

| Issue | File | Handling |
|---|---|---|
| Duplicate `customer_id` rows | customers.csv | `DISTINCT ON (customer_id)` in `stg_customers` |
| Invalid email format (no `@`) | customers.csv | Set to NULL in `stg_customers` |
| Negative `unit_cost` | products.csv | Set to NULL in `stg_products` |
| NULL `customer_id` on orders | orders.csv | Kept as "guest orders" with `is_guest_order = true` |
| Zero / negative `quantity` | order_items.csv | Flagged; excluded from revenue calculations |
| Discount outside [0,1] | order_items.csv | Clamped with `GREATEST(0, LEAST(1, …))` |

---

## c) How to Run

### Prerequisites
- Docker Desktop (or Docker Engine + Compose v2)
- Git

### Default — fully local (Windows / Linux / macOS)

```bash
git clone https://github.com/jaiswalrohit491/salesretail-skypoint-rohit.git
cd retail-pipeline

docker compose up --build
```

No `.env` file needed. Docker Compose starts a local PostgreSQL container,
loads all CSVs, and runs DBT automatically.

**Expected output:**
1. `retail_db` starts and becomes healthy (~5 s)
2. `retail_loader` loads 5 CSVs into `raw` schema, exits 0
3. `retail_dbt` runs `dbt deps` → `dbt run` (10 models) → `dbt test` (40 tests pass), exits 0

**Approximate runtime:** 3–5 min on first build. ~30 s on subsequent runs.

**Persistent data:** the `retail_pgdata` Docker volume survives container restarts.

### Optional — Neon cloud PostgreSQL (macOS + Power BI Service)

If Power BI Desktop is unavailable (macOS), you can route the pipeline to a
free [Neon](https://neon.tech) cloud database so Power BI Service can connect
directly without a gateway.

```bash
cp .env.example .env
# Edit .env — uncomment and fill in the Neon block
docker compose up --build
```

The `db` service is still started but the loader and DBT will connect to Neon
instead. Power BI Service connects to Neon directly.

### Re-running after data changes

```bash
# Replace CSVs in landing/, then:
docker compose up loader dbt
```

---

## d) Power BI Connection Details

### Windows — Power BI Desktop (connects to local Docker DB)

| Setting | Value |
|---|---|
| Server | `localhost` |
| Port | `5432` |
| Database | `retail` |
| Schema | `marts_marts` |
| Username | `retail` |
| Password | `retail_pass` |

Steps: **Get Data → PostgreSQL database → localhost:5432 / retail**
Select tables from `marts_marts`: `dim_customer`, `dim_product`, `dim_store`, `dim_date`, `fact_sales`

### macOS — Power BI Service (connects to Neon cloud DB)

| Setting | Value |
|---|---|
| Server | `ep-curly-poetry-aqxm9hj1.c-8.us-east-1.aws.neon.tech` |
| Port | `5432` |
| Database | `neondb` |
| Schema | `marts_marts` |
| Username | `username` |
| Password | `password` |

> The included `.pbix` file (`powerbi/Retail Sales Analytics Rohit Sah.pbix`)
> is pre-configured for the Neon connection. On Windows, open it in Power BI Desktop
> and update the data source via **Transform Data → Data Source Settings** to point
> to `localhost:5432` after running `docker compose up --build`.

---

## e) Data Model

### Star Schema

```
              dim_date (date_id PK)
                   │
dim_customer ──────┤
(customer_sk PK)   │
                   ▼
dim_store ────► fact_sales ◄──── dim_product
(store_sk PK)  (order_id,        (product_sk PK)
               product_id grain)
```

### Fact Table: `fact_sales`

**Grain:** one row per order line item (`order_id` + `product_id`)

| Column | Description |
|---|---|
| `order_id` | Degenerate dimension – links back to raw order |
| `customer_sk` | FK → `dim_customer` (NULL for guest orders) |
| `product_sk` | FK → `dim_product` |
| `store_sk` | FK → `dim_store` |
| `date_id` | FK → `dim_date` (YYYYMMDD integer) |
| `quantity` | Units sold |
| `discount_pct` | Fractional discount applied (0–1) |
| `gross_revenue` | `unit_price × quantity` |
| `net_revenue` | `gross_revenue × (1 – discount_pct)` |
| `cogs` | `unit_cost × quantity` |
| `gross_profit` | `net_revenue – cogs` |
| `discount_amount` | `gross_revenue – net_revenue` |
| `status` | Order status (completed / returned / cancelled / pending) |
| `is_guest_order` | TRUE when no customer was associated |

**Business logic notes:**
- Cancelled and returned orders are **included** in the fact (with their `status` flag)
- Lines with `quantity ≤ 0` are **excluded** (data quality issues)
- Products with missing `unit_cost` still appear; `gross_profit` will be NULL for those lines

### Dimensions

| Dimension | Key | Notable columns |
|---|---|---|
| `dim_customer` | `customer_sk` | `customer_cohort` (New / Established / Loyal) |
| `dim_product` | `product_sk` | `gross_margin_pct`, `price_tier` |
| `dim_store` | `store_sk` | `region`, `country_code` |
| `dim_date` | `date_id` | `year`, `month_name`, `quarter_label`, `is_weekend` |

---

## f) DAX Measures

| Measure | Formula | Business Question Answered |
|---|---|---|
| `Total Revenue` | `SUM(fact_sales[net_revenue])` | What are total sales by store / category / month? |
| `Total Gross Profit` | `SUM(fact_sales[gross_profit])` | How much profit after cost of goods? |
| `Total Units Sold` | `SUM(fact_sales[quantity])` | Volume of units moved across any slice |
| `Gross Margin %` | `DIVIDE([Total Gross Profit], [Total Revenue])` | Which products / categories have highest and lowest margins? |
| `Avg Order Value` | `DIVIDE([Total Revenue], DISTINCTCOUNT(fact_sales[order_id]))` | What is the average basket size? |
| `Revenue YTD` | `TOTALYTD([Total Revenue], dim_date[full_date])` | How does current year-to-date revenue compare? |
| `MoM Revenue %` | `DIVIDE(cur - prev, prev)` via `DATEADD(-1, MONTH)` | How does sales performance trend month-over-month? |

---

## g) Tech Stack

| Component | Technology | Version |
|---|---|---|
| Database (local) | PostgreSQL | 16-alpine (Docker) |
| Database (cloud) | Neon serverless PostgreSQL | — |
| Loader | Python / psycopg2-binary | 3.12 / 2.9.9 |
| Transformations | dbt-postgres | 1.8.2 |
| DBT utility package | dbt-labs/dbt_utils | 1.3.3 |
| Orchestration | Docker Compose | v2 |
| BI layer | Power BI Service (macOS) / Power BI Desktop (Windows) | Latest |
| Data generation | Python stdlib (csv, random) | 3.x |

---

## h) Screenshots

### Page 1 — Retail Sales Dashboard
![Retail Sales Dashboard](powerbi/screenshots/Retail%20Sales%20Analytics%20Rohit%20Sah_page-0001.jpg)

### Page 2 — Product Margin Detail
![Product Margin Table](powerbi/screenshots/Retail%20Sales%20Analytics%20Rohit%20Sah_page-0002.jpg)

---

## i) Known Limitations

1. **Power BI Desktop / macOS:** Power BI Desktop is Windows-only. On macOS, Power BI Service (browser) was used instead, connected to a Neon cloud database. A Windows assessor can run the full local stack and connect Power BI Desktop to `localhost:5432`.

2. **Two-page report:** The requirement specifies one page. A Product Margin Detail table was added as Page 2 to surface the highest/lowest margin products. The primary executive dashboard is Page 1.

3. **Loader is full-refresh:** Every `docker compose up` drops and recreates raw tables. Incremental loading would require a tool like Airbyte or dbt incremental models.

4. **No orchestration scheduler:** The pipeline is triggered manually. Production use would wrap this in Airflow, Prefect, or a cron job.

5. **Date spine scope:** `dim_date` covers 2018–2025. Orders outside that range would have a NULL `date_id` join.

6. **Guest orders:** ~1% of orders have no `customer_id`. Included in the fact with `is_guest_order = true` but cannot be attributed to a customer dimension row.
