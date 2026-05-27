# Power BI Setup

## Connection

Open `retail_sales.pbix` in Power BI Desktop (Windows).

If the file prompts for credentials or a server change:

1. Go to **Home → Transform Data → Data Source Settings**
2. Select the PostgreSQL source and click **Change Source**
3. Set:
   - Server: `localhost:5432`
   - Database: `retail`
4. Click **Edit Permissions → Edit** and enter:
   - Username: `retail`
   - Password: `retail_pass`
5. Click **Close & Apply** and then **Refresh**

## Tables to import

Select all five tables from the `marts` schema:

- `dim_customer`
- `dim_product`
- `dim_store`
- `dim_date`
- `fact_sales`

## Relationships (set in Model view)

| From | To | Cardinality |
|---|---|---|
| `fact_sales[customer_sk]` | `dim_customer[customer_sk]` | Many-to-one |
| `fact_sales[product_sk]`  | `dim_product[product_sk]`  | Many-to-one |
| `fact_sales[store_sk]`    | `dim_store[store_sk]`      | Many-to-one |
| `fact_sales[date_id]`     | `dim_date[date_id]`        | Many-to-one |

> Set cross-filter direction to **Single** for all relationships.
> The `fact_sales → dim_customer` relationship should use **Assume referential integrity = OFF**
> because ~1% of orders are guest orders with a NULL `customer_sk`.
