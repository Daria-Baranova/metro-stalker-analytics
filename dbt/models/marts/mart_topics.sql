with reviews as (
    select
        fct.player_id,
        fct.language,
        fct.is_positive,
        fct.review_text,
        games.role,
        games.is_exodus
    from {{ ref('fct_reviews') }} as fct
    inner join {{ ref('dim_games') }} as games on fct.appid = games.appid
),

common_reviews as (
    -- C_english: англійські відгуки на Exodus від гравців з англійським відгуком на S.T.A.L.K.E.R. 2
    select exodus.is_positive, exodus.review_text
    from reviews as exodus
    inner join reviews as base on exodus.player_id = base.player_id
    where exodus.is_exodus
        and exodus.language = 'english'
        and base.role = 'base'
        and base.language = 'english'
),

totals as (
    select
        count(*) filter (where is_positive) as n_positive,
        count(*) filter (where not is_positive) as n_negative
    from common_reviews
),

mentions as (
    select
        topics.topic,
        topics.topic_name,
        count(*) filter (where common_reviews.is_positive) as x_positive,
        count(*) filter (where not common_reviews.is_positive) as x_negative
    from {{ ref('topics') }} as topics
    left join common_reviews on common_reviews.review_text ~* topics.pattern
    group by topics.topic, topics.topic_name
)

select
    mentions.topic,
    mentions.topic_name,
    totals.n_positive,
    mentions.x_positive,
    ({{ share('x_positive', 'n_positive') }})::numeric(10, 4) as share_positive,
    ({{ ci_low('x_positive', 'n_positive') }})::numeric(10, 4) as share_positive_ci_low,
    ({{ ci_high('x_positive', 'n_positive') }})::numeric(10, 4) as share_positive_ci_high,
    totals.n_negative,
    mentions.x_negative,
    ({{ share('x_negative', 'n_negative') }})::numeric(10, 4) as share_negative,
    ({{ ci_low('x_negative', 'n_negative') }})::numeric(10, 4) as share_negative_ci_low,
    ({{ ci_high('x_negative', 'n_negative') }})::numeric(10, 4) as share_negative_ci_high
from mentions
cross join totals