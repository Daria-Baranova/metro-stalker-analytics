select
    comment_id,
    compound,
    case
        when compound >= {{ var('vader_positive') }} then 'positive'
        when compound <= {{ var('vader_negative') }} then 'negative'
        else 'neutral'
    end as sentiment
from {{ source('bronze', 'comment_sentiment') }}