select month, count(*) as expected_quarters,
    count(*) filter (where not price_complete) as missing_price_quarters,
    count(*) filter (where not power_complete) as incomplete_power_quarters,
    count(*) filter (where negative_price) as negative_price_quarters,
    count(*) filter (where wind_solar_load_ratio > 1) as wind_solar_exceeds_load_quarters
from {{ ref('fct_market_quarter') }} group by month
