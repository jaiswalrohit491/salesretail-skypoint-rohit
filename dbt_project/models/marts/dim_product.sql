-- Dimension: Product
-- Grain: one row per product_id
with products as (
    select * from {{ ref('stg_products') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['product_id']) }}          as product_sk,
    product_id,
    product_name,
    category,
    sub_category,
    unit_cost,
    unit_price,
    -- Gross margin % (null when cost is missing)
    case
        when unit_cost is not null and unit_cost > 0 and unit_price is not null
        then round(((unit_price - unit_cost) / unit_price) * 100, 2)
        else null
    end                                                              as gross_margin_pct,
    -- Price tier
    case
        when unit_price < 20                then 'Budget'
        when unit_price between 20 and 100  then 'Mid-range'
        when unit_price between 100 and 300 then 'Premium'
        else 'Luxury'
    end                                                              as price_tier
from products
