select count(*) as observed
from {{ ref('fct_market_quarter') }}
having count(*) != 35040
