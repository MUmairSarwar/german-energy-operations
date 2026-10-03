select * from {{ ref('mart_schedule') }}
where gross_difference_eur_per_mw < -0.000001
   or best_start_hour not between 6 and 18 or candidate_count != 13
