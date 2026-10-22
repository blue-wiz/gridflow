-- Latest version of the OWID energy file, typed, countries only (aggregates like "World",
-- "Europe" or "High-income countries" have no ISO code or an OWID_ code and are dropped).
with latest as (
    select max(load_id) as load_id from {{ source('raw', 'load_log') }} where source = 'owid_energy'
)
select
    record ->> 'iso_code'                       as iso_code,
    record ->> 'country'                        as country,
    (record ->> 'year')::int                    as year,
    {{ json_num('population') }}                as population,
    {{ json_num('electricity_generation') }}    as electricity_twh,
    {{ json_num('coal_electricity') }}          as coal_twh,
    {{ json_num('gas_electricity') }}           as gas_twh,
    {{ json_num('oil_electricity') }}           as oil_twh,
    {{ json_num('nuclear_electricity') }}       as nuclear_twh,
    {{ json_num('hydro_electricity') }}         as hydro_twh,
    {{ json_num('wind_electricity') }}          as wind_twh,
    {{ json_num('solar_electricity') }}         as solar_twh,
    {{ json_num('biofuel_electricity') }}       as bioenergy_twh,
    {{ json_num('other_renewable_exc_biofuel_electricity') }} as other_renewable_twh,
    {{ json_num('low_carbon_share_elec') }}     as low_carbon_share_elec_pct,
    {{ json_num('renewables_share_elec') }}     as renewables_share_elec_pct,
    {{ json_num('carbon_intensity_elec') }}     as carbon_intensity_g_per_kwh,
    {{ json_num('primary_energy_consumption') }} as primary_energy_twh,
    {{ json_num('fossil_share_energy') }}       as fossil_share_energy_pct
from {{ source('raw', 'owid_energy') }} e
join latest using (load_id)
where record ->> 'iso_code' is not null
  and record ->> 'iso_code' not like 'OWID%'
