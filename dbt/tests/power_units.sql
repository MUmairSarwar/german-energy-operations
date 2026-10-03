select * from {{ ref('fct_market_quarter') }}
where load_mwh <= 0 or wind_solar_mwh < 0
   or abs(load_mwh - load_mw * 0.25) > 0.000001
