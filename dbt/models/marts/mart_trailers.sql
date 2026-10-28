with labeled as (
    select
        comments.video_id,
        sentiment.sentiment
    from {{ ref('stg_comments') }} as comments
    inner join {{ ref('stg_comment_sentiment') }} as sentiment
        on comments.comment_id = sentiment.comment_id
),

counts as (
    select
        video_id,
        count(*) as n_comments,
        count(*) filter (where sentiment = 'neutral') as n_neutral,
        count(*) filter (where sentiment <> 'neutral') as n_opinion,
        count(*) filter (where sentiment = 'positive') as n_positive,
        count(*) filter (where sentiment = 'negative') as n_negative
    from labeled
    group by video_id
)

select
    videos.video_id,
    videos.title,
    counts.n_comments,
    counts.n_neutral,
    counts.n_opinion,
    counts.n_positive,
    counts.n_negative,
    ({{ share('n_positive', 'n_opinion') }})::numeric(10, 4) as positive_share,
    ({{ ci_low('n_positive', 'n_opinion') }})::numeric(10, 4) as positive_share_ci_low,
    ({{ ci_high('n_positive', 'n_opinion') }})::numeric(10, 4) as positive_share_ci_high
from counts
inner join {{ ref('videos') }} as videos
    on counts.video_id = videos.video_id