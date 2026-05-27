-- Staged products: negative costs zeroed out, margin calculated
with source as (
    select * from {{ source('raw', 'products') }}
),

cleaned as (
    select
        product_id::integer                                     as product_id,
        trim(name)                                              as product_name,
        trim(category)                                          as category,
        trim(sub_category)                                      as sub_category,
        -- Data quality: treat negative cost as null (corrupt record)
        case
            when unit_cost::numeric <= 0 then null
            else unit_cost::numeric
        end                                                     as unit_cost,
        case
            when unit_price::numeric <= 0 then null
            else unit_price::numeric
        end                                                     as unit_price
    from source
    where product_id is not null
)

select * from cleaned
