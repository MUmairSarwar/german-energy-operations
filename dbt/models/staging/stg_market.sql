-- One row per expected UTC quarter-hour; absent source data remains NULL.
select
    s.*,
    p.price_eur_mwh,
    p.source_interval_minutes,
    g.load_mw,
    g.solar_mw,
    g.wind_onshore_mw,
    g.wind_offshore_mw,
    p.price_eur_mwh is not null as price_complete,
    g.load_mw is not null and g.solar_mw is not null
      and g.wind_onshore_mw is not null and g.wind_offshore_mw is not null as power_complete
from {{ source('raw', 'time_spine') }} s
left join {{ source('raw', 'prices') }} p using (ts_utc)
left join {{ source('raw', 'power') }} g using (ts_utc)
