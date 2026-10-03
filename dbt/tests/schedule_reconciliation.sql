with actual as (
 select s.local_date,
   sum(case when f.local_hour >= s.best_start_hour and f.local_hour < s.best_start_hour+4
       then f.cost_eur_per_mw end) as recomputed
 from {{ ref('mart_schedule') }} s
 join {{ ref('fct_market_quarter') }} f using(local_date)
 group by s.local_date
)
select s.* from {{ ref('mart_schedule') }} s join actual a using(local_date)
where abs(s.flexible_cost_eur_per_mw-a.recomputed) > 0.000001
