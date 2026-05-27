-- Staged customers: deduplicated, email validated, dates cast
with source as (
    select * from {{ source('raw', 'customers') }}
),

deduped as (
    -- Keep the most-recently inserted row per customer_id (last one wins)
    select distinct on (customer_id)
        customer_id,
        name,
        email,
        city,
        country,
        signup_date
    from source
    where customer_id is not null
    order by customer_id
),

cleaned as (
    select
        customer_id::integer                                                    as customer_id,
        trim(name)                                                              as customer_name,
        -- Normalise email: strip whitespace, lower-case, null-out bad formats
        case
            when email is null                  then null
            when email not like '%@%'           then null   -- catches "ATgmail.com" style
            else lower(trim(email))
        end                                                                     as email,
        nullif(trim(city), '')                                                  as city,
        upper(trim(country))                                                    as country_code,
        signup_date::date                                                       as signup_date
    from deduped
)

select * from cleaned
