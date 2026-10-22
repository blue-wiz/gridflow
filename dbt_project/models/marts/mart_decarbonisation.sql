-- Who decarbonised their electricity fastest? Compares 2010 with the latest year that has
-- good coverage. Only countries generating at least 10 TWh a year are ranked.
with coverage as (
    select year, count(*) as n from {{ ref('fct_country_year') }}
    where carbon_intensity_g_per_kwh is not null group by year
),
latest_year as (select max(year) as y from coverage where n >= 150),
base as (select * from {{ ref('fct_country_year') }} where year = 2010),
latest as (select f.* from {{ ref('fct_country_year') }} f join latest_year l on f.year = l.y)
select
    l.iso_code, d.country, l.year as latest_year,
    l.electricity_twh,
    b.low_carbon_share_elec_pct                 as low_carbon_share_2010,
    l.low_carbon_share_elec_pct                 as low_carbon_share_latest,
    round(l.low_carbon_share_elec_pct - b.low_carbon_share_elec_pct, 1) as low_carbon_change_pp,
    b.carbon_intensity_g_per_kwh                as carbon_intensity_2010,
    l.carbon_intensity_g_per_kwh                as carbon_intensity_latest,
    round(100 * (l.carbon_intensity_g_per_kwh / nullif(b.carbon_intensity_g_per_kwh, 0) - 1), 1) as carbon_intensity_change_pct,
    rank() over (order by l.low_carbon_share_elec_pct - b.low_carbon_share_elec_pct desc) as rank_low_carbon_gain
from latest l
join base b using (iso_code)
join {{ ref('dim_country') }} d using (iso_code)
where l.electricity_twh >= 10
  and l.low_carbon_share_elec_pct is not null and b.low_carbon_share_elec_pct is not null
