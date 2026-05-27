-- Asserts discount_pct is always between 0 and 1 in the fact table
select order_id, product_id, discount_pct
from {{ ref('fact_sales') }}
where discount_pct < 0 or discount_pct > 1
