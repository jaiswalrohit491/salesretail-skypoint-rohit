-- Staged orders: filter orphaned (null customer) orders to a flag rather than drop,
-- cast types, normalise status
with source as (
    select * from {{ source('raw', 'orders') }}
),

cleaned as (
    select
        order_id::integer                               as order_id,
        customer_id::integer                            as customer_id,
        store_id::integer                               as store_id,
        order_date::date                                as order_date,
        lower(trim(status))                             as status,
        customer_id is null                             as is_guest_order
    from source
    where order_id is not null
)

select * from cleaned
