# Learn and explain the project

## A 90-second explanation

“This project studies whether a flexible four-hour operating schedule could reduce wholesale electricity costs in a historical scenario. It uses public German power data and DE-LU prices. I structured it as a reproducible Python and dbt pipeline with a DuckDB warehouse, rather than a single notebook. The important modelling challenge is the October 2025 transition from hourly to quarter-hourly prices and the daylight-saving changes. The dashboard compares a fixed baseline with the lowest-cost permitted continuous block. The results are energy-only scenario differences, not real savings.”

Use this explanation only after you can demonstrate the implementation yourself.

## Study sequence

1. Run the offline pipeline. Read `reports/executive_summary.md` and identify every scenario assumption.
2. Inspect `data/provenance.json`. Explain why a source hash matters when an API can revise historical data.
3. Read `normalize.py`. Hand-calculate how −20 EUR/MWh for one hour becomes four quarters while preserving cost.
4. Read `stg_market.sql`. Explain why a left join to a complete time spine reveals missing records.
5. Read `mart_schedule.sql`. Explain window frames, `count`, continuity checks and deterministic ties.
6. Run the tests. Remove one source price in a disposable copy and observe how coverage fails; never change the published snapshot without updating provenance.
7. In the dashboard, increase rescheduling cost until adjusted benefit becomes negative. Explain why this is a sensitivity analysis, not a net-profit forecast.
8. Explain why realized generation is descriptive context and must not enter a historical day-ahead scheduling decision.

## Questions to answer without reading notes

- Why is a row average of the raw prices wrong across the 2025 resolution change?
- Why must UTC be the join key rather than an unqualified local timestamp?
- How do MW, MWh and EUR/MWh combine?
- Why is a negative electricity price not a data-quality failure?
- Why can wind-plus-solar divided by load exceed 100%?
- Why is the lowest-cost block not necessarily operationally feasible?
- What would be required for a real point-in-time backtest? (publication-time snapshots, revisions and actual contract/operating constraints)
- What changes for a 100 kW process or weekends without production?

## Substantive next improvements you can own

1. Add a weekend operating calendar and test excluded days.
2. Re-optimize the schedule after start-change costs instead of merely subtracting them.
3. Import CSV marts into Power BI Desktop and build a reviewed semantic model; Power BI is not currently implemented here.
4. Add a second year's data only after generalizing the date and resolution contracts.
5. Add customer-supplied meter data only with appropriate permission and without publishing private information.
