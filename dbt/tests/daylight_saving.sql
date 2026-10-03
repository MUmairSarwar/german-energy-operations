select * from {{ ref('dim_date') }}
where expected_hours != case
    when local_date = date '2025-03-30' then 23
    when local_date = date '2025-10-26' then 25
    else 24 end
