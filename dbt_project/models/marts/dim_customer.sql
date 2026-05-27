-- Dimension: Customer
-- Grain: one row per customer_id
-- Includes a surrogate key for the BI layer
with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }}     as customer_sk,
    customer_id,
    customer_name,
    email,
    city,
    country_code,
    signup_date,
    date_part('year', signup_date)::integer                     as signup_year,
    -- Cohort bucket (years since signup)
    case
        when signup_date >= current_date - interval '1 year'  then 'New (< 1 yr)'
        when signup_date >= current_date - interval '3 years' then 'Established (1–3 yr)'
        else 'Loyal (3+ yr)'
    end                                                          as customer_cohort
from customers
