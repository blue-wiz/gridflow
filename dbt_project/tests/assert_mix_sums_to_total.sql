-- Where every source is reported, the sources must add up to total generation (within 2%).
-- Returns failing country-years.
with sums as (
    select iso_code, year, sum(twh) as source_sum, count(*) as n_sources
    from {{ ref('mart_electricity_mix') }} group by iso_code, year
)
select s.*, f.electricity_twh
from sums s join {{ ref('fct_country_year') }} f using (iso_code, year)
where s.n_sources = 9 and f.electricity_twh > 1
  and abs(s.source_sum - f.electricity_twh) > 0.02 * f.electricity_twh
