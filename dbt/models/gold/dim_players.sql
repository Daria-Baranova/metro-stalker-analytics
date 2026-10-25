with players as (
    select
        player_id,
        max(author_num_reviews) as num_reviews
    from {{ ref('stg_reviews') }}
    group by player_id
)

select
    players.player_id,
    players.num_reviews,
    groups.activity_group,
    groups.sort_order as activity_sort
from players
left join {{ ref('activity_groups') }} as groups
    on players.num_reviews >= groups.min_reviews
    and (groups.max_reviews is null or players.num_reviews <= groups.max_reviews)