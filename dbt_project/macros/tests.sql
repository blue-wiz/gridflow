{# Generic test: column values must fall in [min_value, max_value] (nulls allowed). #}
{% test accepted_range(model, column_name, min_value, max_value) %}
select * from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})
{% endtest %}

{# Generic test: a combination of columns must be unique. #}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
