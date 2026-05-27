-- Staged stores: trim whitespace, cast dates
with source as (
    select * from {{ source('raw', 'stores') }}
),

cleaned as (
    select
        store_id::integer           as store_id,
        trim(name)                  as store_name,
        trim(region)                as region,
        upper(trim(country))        as country_code,
        opened_date::date           as opened_date
    from source
    where store_id is not null
)

select * from cleaned
