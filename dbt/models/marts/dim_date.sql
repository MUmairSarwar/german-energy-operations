select local_date, min(month) as month, min(weekday) as weekday,
       count(*) * 0.25 as expected_hours
from {{ source('raw', 'time_spine') }}
group by local_date
