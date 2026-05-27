-- Asserts that no completed orders have negative net_revenue
-- (returned/cancelled orders may have been excluded downstream but shouldn't
--  have negative values in the fact; discount is capped at 100%)
select
    order_id,
    product_id,
    net_revenue
from {{ ref('fact_sales') }}
where status = 'completed'
  and net_revenue < 0
