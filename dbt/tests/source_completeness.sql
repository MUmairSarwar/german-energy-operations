-- Hard gate for this fixed historical snapshot. Refreshes must resolve missing data.
select * from {{ ref('fct_market_quarter') }}
where not price_complete or not power_complete
