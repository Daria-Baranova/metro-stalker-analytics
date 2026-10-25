select
    appid,
    game_name,
    role,
    is_exodus
from {{ ref('games') }}