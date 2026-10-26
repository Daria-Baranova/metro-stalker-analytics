with stats as (
    select
        *,
        {{ share('x_c', 'n_c') }} as pos_c,
        {{ share('x_o', 'n_o') }} as pos_o
    from {{ ref('int_satisfaction_counts') }}
)

select
    segment,
    n_c,
    x_c,
    n_o,
    x_o,
    pos_c::numeric(10, 4) as pos_c,
    pos_o::numeric(10, 4) as pos_o,
    ((pos_c - pos_o) * 100)::numeric(10, 2) as delta_pp,
    (({{ diff_ci_bound('x_c', 'n_c', 'x_o', 'n_o', '-') }}) * 100)::numeric(10, 2) as delta_pp_ci_low,
    (({{ diff_ci_bound('x_c', 'n_c', 'x_o', 'n_o', '+') }}) * 100)::numeric(10, 2) as delta_pp_ci_high
from stats