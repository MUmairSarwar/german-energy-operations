## Method and decision contract

**Question:** How much gross day-ahead energy cost difference appears in a historical simulation when a fixed four-hour process can change its start time?

### Data grain and geography

- Prices: DE-LU bidding zone, EUR/MWh. Power: German national series, MW. These geographic scopes differ; national generation is descriptive context only.
- Every interval is keyed by its **UTC start**. Local operating dates/hours use Europe/Berlin. Explicit UTC offsets distinguish repeated autumn hours.
- Before 1 October 2025 local time, one hourly price applies to four quarter-hours. On and after that date, prices are native 15-minute values. Missing intervals are never bridged using the next timestamp.
- Power is quarter-hour average MW. Energy in a quarter = MW × 0.25 hours. Time-weighted prices divide price × duration by observed duration.
- Wind/solar-to-load ratio = sum(wind+solar MWh) / sum(load MWh), using complete paired intervals. It is not total renewable generation share, a carbon measure, or a site's power mix.

### Scheduling rule

One hypothetical process operates at constant 1 MW for four uninterrupted hours on every calendar day, including weekends. Baseline starts at 08:00. Candidate starts are 06:00, 07:00, …, 18:00, ending no later than 22:00. For each candidate, SQL sums sixteen quarter-hour costs; a window must contain sixteen observed consecutive prices. A day is eligible only if all thirteen candidates exist. `arg_min` selects cost then earliest start as a deterministic tie-breaker.

All admissible windows include the baseline as a candidate, so gross flexible cost cannot exceed baseline cost. Days omitted for missing prices must be reported separately; the provided 2025 snapshot is required to have complete coverage.

The model uses only the delivery day's **day-ahead** prices to select a start. Realized load or generation never enters the decision rule. However, the API returns historical values without original publication/version timestamps. This is a **retrospective price-curve benchmark**, not a proven point-in-time live backtest or price-forecasting model.

### Cost and sensitivity

Energy-only EUR = price EUR/MWh × process MW × duration hours. Gross difference = baseline cost − flexible cost. The dashboard scales power and subtracts an assumed incremental cost per day whose selected start differs from 08:00. It evaluates the original gross-optimal schedule and does **not** re-optimize under that cost. Negative adjusted benefit is valid and highlights sensitivity.

Excluded: grid tariffs, taxes, levies, retail markups, imbalance charges, start/stop costs, ramp rates, minimum runs beyond four hours, staffing and throughput constraints. No actual company/site or savings claim is made. The public-market curves may have been revised.

### Quality gates and lineage

`API snapshot → Python contracts → raw tables → stg_market → fct_market_quarter + dim_date → daily/schedule/quality marts → dashboard/reports`.

Ingestion checks the snapshot SHA-256, required fields, array lengths, unique monotonic timestamps, quarter-hour alignment, finite numbers, price unit, physical sign and non-overlap. Nulls are retained. dbt tests enforce complete 2025 coverage, 35,040 quarters, unique keys, date relationships, 23/25-hour daylight-saving days, unit arithmetic and scheduling cost reconciliation. Negative prices are retained as valid market signals.

### Sources

- [Energy-Charts API and licensing](https://api.energy-charts.info/)
- [SMARD: 15-minute day-ahead prices from 1 October 2025](https://www.smard.de/en/15-minute-wholesale-prices-available-218078)
- [SMARD: summer/winter time](https://www.smard.de/en/change-from-summer-to-winter-time-218202)
- Exact request URLs, source response hashes and snapshot hash: `data/provenance.json`.
