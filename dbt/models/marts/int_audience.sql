with player_metro as (
    select
        fct.player_id,
        bool_or(games.role = 'metro') as has_metro
    from {{ ref('fct_reviews') }} as fct
    inner join {{ ref('dim_games') }} as games on fct.appid = games.appid
    group by fct.player_id
),

base_players as (
    select
        fct.language,
        player_metro.has_metro
    from {{ ref('fct_reviews') }} as fct
    inner join {{ ref('dim_games') }} as games on fct.appid = games.appid
    inner join player_metro on fct.player_id = player_metro.player_id
    where games.role = 'base'
)

select
    language as segment,
    count(*) filter (where not has_metro) as audience_not_played
from base_players
group by language

union all

select
    'eu5' as segment,
    count(*) filter (where not has_metro) as audience_not_played
from base_players
inner join {{ ref('dim_language') }} as languages
    on base_players.language = languages.language
where languages.is_eu5