with reviews as (
    select
        fct.player_id,
        fct.language,
        games.role,
        players.activity_group
    from {{ ref('fct_reviews') }} as fct
    inner join {{ ref('dim_games') }} as games on fct.appid = games.appid
    inner join {{ ref('dim_players') }} as players on fct.player_id = players.player_id
),

player_flags as (
    select
        player_id,
        bool_or(role = 'base') as has_base,
        bool_or(role = 'control') as has_control,
        bool_or(role = 'metro') as has_metro
    from reviews
    group by player_id
),

-- S: S.T.A.L.K.E.R. 2 без Far Cry 5; F: Far Cry 5 без S.T.A.L.K.E.R. 2
study_groups as (
    select
        reviews.language,
        reviews.activity_group,
        case reviews.role when 'base' then 'S' else 'F' end as study_group,
        player_flags.has_metro
    from reviews
    inner join player_flags on reviews.player_id = player_flags.player_id
    where (reviews.role = 'base' and not player_flags.has_control)
        or (reviews.role = 'control' and not player_flags.has_base)
),

segments as (
    select language as segment, * from study_groups
    union all
    select 'eu5' as segment, study_groups.*
    from study_groups
    inner join {{ ref('dim_language') }} as languages
        on study_groups.language = languages.language
    where languages.is_eu5
),

by_activity as (
    select segment, 'all' as activity_group, study_group, has_metro from segments
    union all
    select segment, activity_group, study_group, has_metro
    from segments
    where activity_group <> '1'  -- автор з 1 відгуком не може мати відгук на Metro
)

select
    segment,
    activity_group,
    count(*) filter (where study_group = 'S') as n_s,
    count(*) filter (where study_group = 'S' and has_metro) as x_s,
    count(*) filter (where study_group = 'F') as n_f,
    count(*) filter (where study_group = 'F' and has_metro) as x_f
from by_activity
group by segment, activity_group