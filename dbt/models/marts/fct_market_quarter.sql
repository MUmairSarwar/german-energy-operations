select *,
    case when price_complete then price_eur_mwh * interval_hours end as cost_eur_per_mw,
    case when power_complete then load_mw * interval_hours end as load_mwh,
    case when power_complete then (solar_mw + wind_onshore_mw + wind_offshore_mw) * interval_hours end as wind_solar_mwh,
    case when power_complete then (solar_mw + wind_onshore_mw + wind_offshore_mw) / nullif(load_mw, 0) end as wind_solar_load_ratio,
    case when price_complete then price_eur_mwh < 0 end as negative_price
from {{ ref('stg_market') }}
