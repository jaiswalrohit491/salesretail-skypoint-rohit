-- Staged order items: filter non-positive quantities, clamp discount to [0,1]
with source as (
    select * from {{ source('raw', 'order_items') }}
),

cleaned as (
    select
        order_id::integer                                                           as order_id,
        product_id::integer                                                         as product_id,
        quantity::integer                                                           as quantity,
        -- Clamp discount to sensible range
        greatest(0, least(1, discount_pct::numeric))                               as discount_pct,
        -- Flag rows with bad quantity so analysts can inspect
        quantity::integer <= 0                                                      as is_quantity_invalid
    from source
    where order_id is not null
      and product_id is not null
)

select * from cleaned
