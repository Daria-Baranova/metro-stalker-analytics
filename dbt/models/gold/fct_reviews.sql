select
    reviews.review_id,
    reviews.player_id,
    reviews.appid,
    reviews.language,
    reviews.created_at_utc::date as created_date,
    reviews.is_positive,
    reviews.playtime_h,
    reviews.review_text
from {{ ref('stg_reviews') }} as reviews
inner join {{ ref('dim_language') }} as languages  -- лише 7 мов сегментів
    on reviews.language = languages.language