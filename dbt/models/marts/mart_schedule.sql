-- Illustrative 1 MW process, 4 uninterrupted hours, whole-hour starts 06:00..18:00.
-- Day-ahead prices only; realized load/generation do not drive the schedule.
with windows as (
    select local_date, ts_utc, local_hour,
        sum(cost_eur_per_mw) over w as block_cost,
        count(*) over w as quarters,
        count(price_eur_mwh) over w as priced_quarters,
        max(ts_utc) over w as last_ts
    from {{ ref('fct_market_quarter') }}
    window w as (partition by local_date order by ts_utc rows between current row and 15 following)
), candidates as (
    select * from windows
    where local_hour between 6 and 18 and minute(ts_utc) = 0
      and quarters = 16 and priced_quarters = 16
      and last_ts - ts_utc = interval '225 minutes'
), daily as (
    select local_date, count(*) as candidate_count,
        max(case when local_hour = 8 then block_cost end) as baseline_cost_eur_per_mw,
        min(block_cost) as flexible_cost_eur_per_mw,
        arg_min(local_hour, struct_pack(cost := block_cost, hour := local_hour)) as best_start_hour
    from candidates group by local_date
)
select *, baseline_cost_eur_per_mw - flexible_cost_eur_per_mw as gross_difference_eur_per_mw
from daily
-- Incomplete operating windows are excluded, not treated as zero cost.
where candidate_count = 13 and baseline_cost_eur_per_mw is not null
