with compared as (
    select
        labels.human_label,
        sentiment.sentiment as vader_label
    from {{ ref('vader_labels') }} as labels
    inner join {{ ref('stg_comment_sentiment') }} as sentiment
        on labels.comment_id = sentiment.comment_id
),

counts as (
    select
        count(*) as n_labeled,
        count(*) filter (where human_label = vader_label) as n_match
    from compared
)

select
    n_labeled,
    n_match,
    ({{ share('n_match', 'n_labeled') }})::numeric(10, 4) as accuracy,
    ({{ ci_low('n_match', 'n_labeled') }})::numeric(10, 4) as accuracy_ci_low,
    ({{ ci_high('n_match', 'n_labeled') }})::numeric(10, 4) as accuracy_ci_high
from counts