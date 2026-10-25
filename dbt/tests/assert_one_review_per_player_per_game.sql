-- Steam дозволяє 1 відгук на гру. Якщо тут є рядки — припущення брифу хибне
select
    player_id,
    appid,
    count(*) as reviews
from {{ ref('stg_reviews') }}
group by player_id, appid
having count(*) > 1