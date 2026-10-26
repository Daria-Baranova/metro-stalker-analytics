with reviews as (
    select
        fct.player_id,
        fct.language,
        fct.is_positive,
        games.role,
        games.is_exodus
    from {{ ref('fct_reviews') }} as fct
    inner join {{ ref('dim_games') }} as games on fct.appid = games.appid
),

base_players as (
    select player_id, language
    from reviews
    where role = 'base'
),

exodus_reviews as (
    select player_id, language, is_positive
    from reviews
    where is_exodus
),

study_groups as (
    -- C: гравці S.T.A.L.K.E.R. 2 з відгуком на Exodus; сегмент — мова відгуку на S.T.A.L.K.E.R. 2
    select
        base_players.language,
        'C' as study_group,
        exodus_reviews.is_positive
    from base_players
    inner join exodus_reviews on base_players.player_id = exodus_reviews.player_id

    union all

    -- O: відгук на Exodus без відгуку на S.T.A.L.K.E.R. 2; сегмент — мова відгуку на Exodus
    select
        exodus_reviews.language,
        'O' as study_group,
        exodus_reviews.is_positive
    from exodus_reviews
    left join base_players on exodus_reviews.player_id = base_players.player_id
    where base_players.player_id is null
),

segments as (
    select language as segment, study_group, is_positive from study_groups
    union all
    select 'eu5' as segment, study_groups.study_group, study_groups.is_positive
    from study_groups
    inner join {{ ref('dim_language') }} as languages
        on study_groups.language = languages.language
    where languages.is_eu5
)

select
    segment,
    count(*) filter (where study_group = 'C') as n_c,
    count(*) filter (where study_group = 'C' and is_positive) as x_c,
    count(*) filter (where study_group = 'O') as n_o,
    count(*) filter (where study_group = 'O' and is_positive) as x_o
from segments
group by segment