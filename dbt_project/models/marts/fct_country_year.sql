-- One row per country and year since 1990: electricity mix, carbon intensity and emissions.
select
    e.iso_code, e.year, e.population,
    e.electricity_twh, e.coal_twh, e.gas_twh, e.oil_twh, e.nuclear_twh, e.hydro_twh,
    e.wind_twh, e.solar_twh, e.bioenergy_twh, e.other_renewable_twh,
    e.low_carbon_share_elec_pct, e.renewables_share_elec_pct, e.carbon_intensity_g_per_kwh,
    e.primary_energy_twh, e.fossil_share_energy_pct,
    c.co2_mt, c.co2_per_capita_t, c.total_ghg_mt, c.share_global_co2_pct
from {{ ref('stg_owid_energy') }} e
left join {{ ref('stg_owid_co2') }} c using (iso_code, year)
where e.year >= 1990
