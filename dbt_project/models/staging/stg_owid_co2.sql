with latest as (
    select max(load_id) as load_id from {{ source('raw', 'load_log') }} where source = 'owid_co2'
)
select
    record ->> 'iso_code'                as iso_code,
    (record ->> 'year')::int             as year,
    {{ json_num('co2') }}                as co2_mt,
    {{ json_num('co2_per_capita') }}     as co2_per_capita_t,
    {{ json_num('total_ghg') }}          as total_ghg_mt,
    {{ json_num('share_global_co2') }}   as share_global_co2_pct,
    {{ json_num('gdp') }}                as gdp
from {{ source('raw', 'owid_co2') }}
join latest using (load_id)
where record ->> 'iso_code' is not null
  and record ->> 'iso_code' not like 'OWID%'
