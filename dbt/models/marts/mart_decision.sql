with overlap as (
    select * from {{ ref('mart_overlap') }}
    where activity_group = 'all'
),

checks as (
    select
        overlap.segment,
        overlap.lift,
        overlap.lift_ci_low,
        overlap.lift_ci_high,
        overlap.z,
        overlap.p_value,
        satisfaction.delta_pp,
        satisfaction.delta_pp_ci_low,
        satisfaction.delta_pp_ci_high,
        audience.audience_not_played,
        overlap.n_s,
        overlap.n_f,
        satisfaction.n_c,
        satisfaction.n_o,
        (
            least(overlap.n_s, overlap.n_f, satisfaction.n_c, satisfaction.n_o)
                < {{ var('min_group_n') }}
            or least(overlap.x_s, overlap.x_f, satisfaction.x_c, satisfaction.x_o)
                < {{ var('min_group_x') }}
            or least(
                overlap.n_s - overlap.x_s, overlap.n_f - overlap.x_f,
                satisfaction.n_c - satisfaction.x_c, satisfaction.n_o - satisfaction.x_o
            ) < {{ var('min_group_x') }}
        ) as is_low_data,
        coalesce(
            overlap.lift >= {{ var('lift_threshold') }}
            and abs(overlap.z) >= {{ var('z_bonferroni') }},
            false
        ) as condition_a,
        coalesce(satisfaction.delta_pp >= {{ var('satisfaction_delta_pp') }}, false) as condition_b
    from overlap
    inner join {{ ref('mart_satisfaction') }} as satisfaction
        on overlap.segment = satisfaction.segment
    inner join {{ ref('int_audience') }} as audience
        on overlap.segment = audience.segment
),

labeled as (
    select
        *,
        case
            when is_low_data then 'Мало даних'
            when condition_a and condition_b then 'Так'
            when condition_a then 'Тестово'
            else 'Ні'
        end as label
    from checks
),

scenario as (
    select
        max(label) filter (where segment = 'english') as english_label,
        max(label) filter (where segment = 'eu5') as eu5_label
    from labeled
),

fallback as (
    -- «Мало даних» бере рішення рядка «5 мов ЄС»
    select
        labeled.*,
        scenario.english_label,
        case when labeled.label = 'Мало даних' then scenario.eu5_label else labeled.label end
            as base_label
    from labeled
    cross join scenario
),

effective as (
    -- english = Ні → гіпотеза провалена → «Так» лише як A/B-тест
    select
        *,
        case when base_label = 'Так' and english_label = 'Ні' then 'Тестово' else base_label end
            as action_label
    from fallback
)

select
    effective.segment,
    effective.label,
    case
        when effective.label = 'Мало даних' then 'За «5 мов ЄС»: ' || actions.action
        else actions.action
    end as action,
    case when effective.condition_a then 'A ✓' else 'A ✗' end
        || ' · '
        || case when effective.condition_b then 'B ✓' else 'B ✗' end as reason,
    labels.priority,
    effective.lift,
    effective.lift_ci_low,
    effective.lift_ci_high,
    effective.z,
    effective.p_value,
    effective.delta_pp,
    effective.delta_pp_ci_low,
    effective.delta_pp_ci_high,
    effective.audience_not_played,
    effective.n_s,
    effective.n_f,
    effective.n_c,
    effective.n_o
from effective
inner join {{ ref('decision_labels') }} as labels
    on effective.label = labels.label
inner join {{ ref('decision_labels') }} as actions
    on effective.action_label = actions.label