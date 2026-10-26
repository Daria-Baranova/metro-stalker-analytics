with stats as (
    select
        *,
        {{ share('x_s', 'n_s') }} as p_s,
        {{ share('x_f', 'n_f') }} as p_f,
        {{ z_two_prop('x_s', 'n_s', 'x_f', 'n_f') }} as z
    from {{ ref('int_overlap_counts') }}
)

select
    segment,
    activity_group,
    n_s,
    x_s,
    n_f,
    x_f,
    p_s::numeric(10, 4) as p_s,
    ({{ ci_low('x_s', 'n_s') }})::numeric(10, 4) as p_s_ci_low,
    ({{ ci_high('x_s', 'n_s') }})::numeric(10, 4) as p_s_ci_high,
    p_f::numeric(10, 4) as p_f,
    ({{ ci_low('x_f', 'n_f') }})::numeric(10, 4) as p_f_ci_low,
    ({{ ci_high('x_f', 'n_f') }})::numeric(10, 4) as p_f_ci_high,
    (p_s / nullif(p_f, 0))::numeric(10, 4) as lift,
    ({{ lift_ci_bound('x_s', 'n_s', 'x_f', 'n_f', '-') }})::numeric(10, 4) as lift_ci_low,
    ({{ lift_ci_bound('x_s', 'n_s', 'x_f', 'n_f', '+') }})::numeric(10, 4) as lift_ci_high,
    z::numeric(10, 4) as z,
    ({{ p_value('z') }})::numeric(10, 6) as p_value
from stats