select f.local_date, d.month, d.weekday, d.expected_hours,
    count(*) as intervals,
    sum(case when price_complete then interval_hours else 0 end) as priced_hours,
    sum(case when power_complete then interval_hours else 0 end) as power_hours,
    sum(cost_eur_per_mw) / nullif(sum(case when price_complete then interval_hours else 0 end), 0) as mean_price_eur_mwh,
    sum(case when negative_price then interval_hours else 0 end) as negative_price_hours,
    sum(load_mwh) as observed_load_mwh,
    sum(wind_solar_mwh) / nullif(sum(load_mwh), 0) as wind_solar_load_ratio
from {{ ref('fct_market_quarter') }} f
join {{ ref('dim_date') }} d using (local_date)
group by f.local_date, d.month, d.weekday, d.expected_hours
