-- Dimension: Date
-- Grain: one row per calendar date spanning 2018-01-01 → 2025-12-31
-- Generated entirely in SQL (no seeds required)
with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2018-01-01' as date)",
        end_date="cast('2026-01-01' as date)"
    ) }}
)

select
    to_char(date_day, 'YYYYMMDD')::integer      as date_id,
    date_day                                     as full_date,
    date_part('year',  date_day)::integer        as year,
    date_part('month', date_day)::integer        as month_number,
    to_char(date_day, 'Month')                   as month_name,
    to_char(date_day, 'Mon')                     as month_short,
    date_part('quarter', date_day)::integer      as quarter,
    'Q' || date_part('quarter', date_day)::text  as quarter_label,
    date_part('week',  date_day)::integer        as iso_week,
    date_part('dow',   date_day)::integer        as day_of_week,   -- 0=Sun
    to_char(date_day, 'Day')                     as day_name,
    date_part('day',   date_day)::integer        as day_of_month,
    date_part('doy',   date_day)::integer        as day_of_year,
    date_part('dow',   date_day)::integer in (0, 6) as is_weekend,
    to_char(date_day, 'YYYY-MM')                 as year_month
from date_spine
