# 2025 German electricity: operating flexibility study

**Decision:** Is a controlled pilot worth evaluating for a process that can move its daily operating block?

This is a retrospective portfolio study using public data. It does not describe a real business, customer meter, investment return or achieved operational saving.

## Measured market facts

- 35,040 aligned quarter-hour records, representing 8,760 hours.
- Time-weighted average DE-LU day-ahead price: **€89.32/MWh**.
- Negative-price duration: **574.75 hours**. Negative values are valid market observations.
- Observed range: €-250.32 to €583.40/MWh.
- German wind-plus-solar generation / load (ratio of energy sums): **43.2%**. This excludes hydro, biomass and other renewables; it is not the total renewable share.

## Explicit scheduling scenario

A hypothetical constant **1 MW** process runs **4 consecutive hours every calendar day**, consuming 4 MWh/day. Baseline: 08:00–12:00 Europe/Berlin. Flexible starts: whole hours from 06:00 through 18:00, finishing by 22:00. The model chooses the lowest-cost block using that delivery day's day-ahead price curve. Equal-cost ties use the earliest start.

Across **365 eligible days**:

| Measure | Energy-only scenario |
|---|---:|
| Baseline cost | €121,261.79 |
| Flexible cost | €69,896.86 |
| Gross difference | €51,364.94 |
| Gross reduction against baseline | 42.4% |
| Days with a different start | 365 |

The gross difference averages **€140.73 per changed day**. That is a break-even ceiling for an assumed constant incremental rescheduling cost, before other omitted costs. It is not an operating-cost estimate. Power scales linearly: a 100 kW process has one tenth of these energy-only costs and differences.

## Decision and pilot design

1. First confirm whether a real process can move four continuous hours without violating throughput, staffing, maintenance or customer deadlines.
2. Verify exposure to these prices in the actual contract. Add grid tariffs, taxes, levies, imbalance costs and start/stop costs before any commercial decision.
3. Run a shadow schedule, record the price curve available at the decision time, and compare predicted versus realized total cost on matched operating days.
4. Proceed only if measured net benefit remains positive and operational service levels are maintained.

## Quality and interpretation

UTC is the join key; local dates and hours drive scheduling. The 23-hour and 25-hour daylight-saving days remain intact. Hourly prices before 1 October are applied to their four constituent quarters; subsequent prices retain their native 15-minute resolution. Missing data is never zero-filled or carried through gaps. The build fails if this fixed snapshot has incomplete coverage.

Day-ahead prices would normally be available before the delivery day, but this historical API download does not preserve original publication timestamps or revisions. Therefore the schedule is a retrospective price-curve benchmark, **not a verified live backtest**. Actual generation/load is used only for descriptive analysis, never to choose the schedule. National aggregate generation does not establish the electricity mix consumed by a particular site. No causal or carbon-emissions claim is made.

Source: Energy-Charts.info; price data credited by API to Bundesnetzagentur / SMARD.de. CC BY 4.0. See [provenance](../data/provenance.json), [data notes](../data/README.md) and [methodology](../docs/methodology.md).
