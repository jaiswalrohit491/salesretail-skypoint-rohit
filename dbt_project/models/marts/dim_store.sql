-- Dimension: Store
-- Grain: one row per store_id
with stores as (
    select * from {{ ref('stg_stores') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['store_id']) }}    as store_sk,
    store_id,
    store_name,
    region,
    country_code,
    opened_date,
    date_part('year', opened_date)::integer                 as open_year
from stores
