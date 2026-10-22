{# Read a numeric field from the raw JSONB record. #}
{% macro json_num(col) -%}
    nullif(record ->> '{{ col }}', '')::numeric
{%- endmacro %}
