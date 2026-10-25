with prices as (
    select * from {{ source('bronze', 'steam_appdetails') }}
),

latest_usd_rate as (
    select uah_per_unit
    from {{ source('bronze', 'nbu_rates') }}
    where currency = 'USD'
    order by rate_date desc
    limit 1
)

select
    prices.appid,
    prices.country,
    prices.name as game_name,
    prices.is_free,
    prices.coming_soon,
    prices.release_date as release_date_text,
    prices.currency,
    prices.price_initial / 100.0 as price_initial_local,
    prices.price_final / 100.0 as price_final_local,
    prices.discount_percent,
    round(
        case prices.currency
            when 'USD' then prices.price_final / 100.0
            when 'UAH' then prices.price_final / 100.0 / latest_usd_rate.uah_per_unit::numeric
        end,
        2
    ) as price_final_usd,
    prices.loaded_at
from prices
left join latest_usd_rate on true