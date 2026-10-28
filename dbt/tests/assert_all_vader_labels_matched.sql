select labels.comment_id
from {{ ref('vader_labels') }} as labels
left join {{ ref('stg_comment_sentiment') }} as sentiment
    on labels.comment_id = sentiment.comment_id
where sentiment.comment_id is null