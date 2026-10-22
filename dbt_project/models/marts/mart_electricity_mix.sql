-- Long format (country, year, source, TWh, share): the shape BI tools want for stacked charts.
with f as (select * from {{ ref('fct_country_year') }} where electricity_twh > 0),
long as (
    {% set sources = ['coal','gas','oil','nuclear','hydro','wind','solar','bioenergy','other_renewable'] %}
    {% for s in sources %}
    select iso_code, year, '{{ s }}' as source, {{ s }}_twh as twh, electricity_twh from f
    {% if not loop.last %}union all{% endif %}
    {% endfor %}
)
select iso_code, year, source, twh,
       round(100 * twh / electricity_twh, 2) as share_pct,
       case when source in ('coal','gas','oil') then 'fossil'
            when source = 'nuclear' then 'nuclear' else 'renewable' end as source_group
from long where twh is not null
