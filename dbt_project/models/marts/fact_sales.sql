-- Fact: Sales
-- Grain: one row per order line item (order_id + product_id)
-- Excludes cancelled orders and invalid quantity rows from revenue metrics
with order_items as (
    select * from {{ ref('stg_order_items') }}
    where not is_quantity_invalid       -- drop 0 / negative qty rows
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

joined as (
    select
        oi.order_id,
        oi.product_id,
        o.customer_id,
        o.store_id,
        o.order_date,
        o.status,
        o.is_guest_order,

        -- surrogate keys (for BI relationships)
        -- NULL-guard: generate_surrogate_key hashes NULL as '' producing a phantom key;
        -- explicitly null out guest orders so the FK join to dim_customer stays clean
        case when o.customer_id is null then null
             else {{ dbt_utils.generate_surrogate_key(['o.customer_id']) }}
        end                                                              as customer_sk,
        {{ dbt_utils.generate_surrogate_key(['oi.product_id']) }}       as product_sk,
        {{ dbt_utils.generate_surrogate_key(['o.store_id']) }}          as store_sk,
        to_char(o.order_date, 'YYYYMMDD')::integer                      as date_id,

        oi.quantity,
        oi.discount_pct,

        -- Revenue & cost calculations
        -- Gross revenue (before discount)
        round(p.unit_price * oi.quantity, 2)                            as gross_revenue,
        -- Net revenue (after discount)
        round(p.unit_price * oi.quantity * (1 - oi.discount_pct), 2)   as net_revenue,
        -- Cost of goods sold
        round(p.unit_cost  * oi.quantity, 2)                            as cogs,
        -- Gross profit
        round(
            (p.unit_price * (1 - oi.discount_pct) - coalesce(p.unit_cost, 0))
            * oi.quantity, 2
        )                                                                as gross_profit,
        -- Discount amount
        round(p.unit_price * oi.quantity * oi.discount_pct, 2)         as discount_amount

    from order_items oi
    inner join orders  o on oi.order_id  = o.order_id
    inner join products p on oi.product_id = p.product_id
    -- Guest orders (null customer) are kept; customer_sk will be null
)

select * from joined
