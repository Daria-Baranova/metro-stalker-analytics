with bounds as (
    select
        min(created_at_utc)::date as first_day,
        ('{{ var("analysis_end_date") }}'::date - 1) as last_day
    from {{ ref('stg_reviews') }}
)

select
    day::date as date_day,
    extract(year from day)::int as year,
    extract(month from day)::int as month,
    date_trunc('month', day)::date as month_start
from bounds,
    generate_series(first_day, last_day, interval '1 day') as day