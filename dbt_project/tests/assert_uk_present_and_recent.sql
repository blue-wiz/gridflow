-- The UK must be in the latest load with data from at least 2020 (catches silent source changes).
select 1 where (select max(year) from {{ ref('fct_country_year') }}
                where iso_code = 'GBR' and electricity_twh is not null) < 2020
