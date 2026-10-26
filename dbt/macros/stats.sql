{% macro share(x, n) -%}
    ({{ x }})::numeric / nullif({{ n }}, 0)
{%- endmacro %}


{% macro ci_bound(x, n, sign) -%}
    {{ share(x, n) }} {{ sign }} {{ var('z_95') }}
        * sqrt({{ share(x, n) }} * (1 - {{ share(x, n) }}) / nullif({{ n }}, 0))
{%- endmacro %}


{% macro ci_low(x, n) -%}
    {{ ci_bound(x, n, '-') }}
{%- endmacro %}


{% macro ci_high(x, n) -%}
    {{ ci_bound(x, n, '+') }}
{%- endmacro %}


{% macro z_two_prop(x1, n1, x2, n2) -%}
    {%- set pooled = share(x1 ~ ' + ' ~ x2, n1 ~ ' + ' ~ n2) -%}
    ({{ share(x1, n1) }} - {{ share(x2, n2) }})
    / nullif(sqrt(
        {{ pooled }} * (1 - {{ pooled }})
        * (1.0 / nullif({{ n1 }}, 0) + 1.0 / nullif({{ n2 }}, 0))
    ), 0)
{%- endmacro %}


{% macro lift_ci_bound(x1, n1, x2, n2, sign) -%}
    exp(
        ln(nullif({{ share(x1, n1) }} / nullif({{ share(x2, n2) }}, 0), 0))
        {{ sign }} {{ var('z_95') }} * sqrt(
            (1 - {{ share(x1, n1) }}) / nullif({{ x1 }}, 0)
            + (1 - {{ share(x2, n2) }}) / nullif({{ x2 }}, 0)
        )
    )
{%- endmacro %}


{% macro p_value(z) -%}
    erfc(abs({{ z }})::float / sqrt(2))
{%- endmacro %}