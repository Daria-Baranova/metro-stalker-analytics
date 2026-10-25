with source as (
    select * from {{ source('bronze', 'steam_reviews') }}
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by recommendationid
            order by timestamp_updated desc, _dlt_load_id desc
        ) as row_num
    from source
)

select
    recommendationid as review_id,
    appid,
    language,
    encode(
        sha256(convert_to(author_steamid || '{{ env_var("HASH_SALT") }}', 'UTF8')),
        'hex'
    ) as player_id,
    voted_up as is_positive,
    review as review_text,
    author_num_reviews,
    round(author_playtime_at_review / 60.0, 1) as playtime_h,
    to_timestamp(timestamp_created) at time zone 'UTC' as created_at_utc,
    to_timestamp(timestamp_updated) at time zone 'UTC' as updated_at_utc
from deduplicated
where row_num = 1
    and to_timestamp(timestamp_created) at time zone 'UTC'
        < '{{ var("analysis_end_date") }}'::timestamp