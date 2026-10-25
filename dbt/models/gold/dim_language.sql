select
    language,
    language_name,
    is_eu5
from {{ ref('languages') }}