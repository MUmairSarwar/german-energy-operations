# Data provenance and licence

Public source: **Energy-Charts.info**, Fraunhofer ISE. API: https://api.energy-charts.info/ . Price response explicitly credits **Bundesnetzagentur / SMARD.de**, CC BY 4.0. The power endpoint uses the API's default CC BY 4.0 licence; source data combines ENTSO-E and other sources described by Energy-Charts.

This repository redistributes a compressed, reduced snapshot under **CC BY 4.0**: https://creativecommons.org/licenses/by/4.0/ . Attribution must be preserved if reused. The MIT code licence does not replace the data licence. No endorsement by the providers is implied.

`snapshot_2025.json.gz` retains the API price response and only four production/load series from the power response (Load, Solar, Wind onshore, Wind offshore). No measurement values are modified in this snapshot. `provenance.json` records exact request URLs, original response hashes, snapshot hash and extraction time. The raw full API responses are not committed. The default build is offline and verifies the snapshot hash before processing.

## Rebuild or refresh

```bash
python -m energy_ops.ingest --refresh
python -m energy_ops.pipeline
```

Refresh explicitly downloads two requests, replaces the snapshot and regenerates its provenance. The API may revise data; review the resulting changes before committing. HTTP failures are surfaced, not silently replaced by synthetic data. Respect the provider's rate limits; this project has no scheduled polling.

## Scope

Delivery dates 2025-01-01 through 2025-12-31 in Europe/Berlin (UTC span 2024-12-31 23:00 inclusive through 2025-12-31 23:00 exclusive). Prices are DE-LU wholesale day-ahead EUR/MWh. Power values are German national interval-average MW. No private employer, university or customer data is used.
