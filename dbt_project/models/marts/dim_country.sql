-- Every country that appears in the energy data. Latest known population where available
-- (some territories have energy data but no population series).
select distinct on (iso_code)
    iso_code, country,
    population as latest_population,
    case when population is not null then year end as population_year
from {{ ref('stg_owid_energy') }}
order by iso_code, (population is null), year desc
