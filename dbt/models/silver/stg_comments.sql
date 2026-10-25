select
    comment_id,
    video_id,
    text as comment_text,
    like_count,
    published_at at time zone 'UTC' as published_at_utc,
    updated_at at time zone 'UTC' as updated_at_utc
from {{ source('bronze', 'youtube_comments') }}
where published_at at time zone 'UTC' < '{{ var("analysis_end_date") }}'::timestamp