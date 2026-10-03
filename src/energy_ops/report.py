"""All published figures and metrics derive from the tested warehouse."""
from __future__ import annotations
import json
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .ingest import ROOT


def export_reports(db_path: Path) -> None:
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    with duckdb.connect(str(db_path), read_only=True) as con:
        frames = {name: con.sql(f'select * from {table} order by 1').df() for name, table in {
            'daily': 'mart_daily', 'schedule': 'mart_schedule', 'quality': 'mart_quality',
        }.items()}
        monthly = con.sql('''select d.month,
            sum(d.mean_price_eur_mwh*d.priced_hours)/sum(d.priced_hours) as mean_price_eur_mwh,
            sum(d.negative_price_hours) as negative_price_hours,
            sum(s.baseline_cost_eur_per_mw) as baseline_cost_eur_per_mw,
            sum(s.flexible_cost_eur_per_mw) as flexible_cost_eur_per_mw,
            sum(s.gross_difference_eur_per_mw) as gross_difference_eur_per_mw
            from mart_daily d left join mart_schedule s using(local_date)
            group by d.month order by d.month''').df()
        metrics = con.sql('''select count(*) as quarter_hours,
          sum(case when price_complete then interval_hours else 0 end) as priced_hours,
          avg(price_eur_mwh) as mean_price_eur_mwh,
          min(price_eur_mwh) as min_price_eur_mwh,
          max(price_eur_mwh) as max_price_eur_mwh,
          sum(case when negative_price then interval_hours else 0 end) as negative_price_hours,
          sum(wind_solar_mwh)/sum(load_mwh) as wind_solar_load_ratio
          from fct_market_quarter''').df().iloc[0].to_dict()
    schedule = frames['schedule']
    metrics.update({
        'eligible_days': len(schedule),
        'baseline_cost_eur_per_mw': float(schedule.baseline_cost_eur_per_mw.sum()),
        'flexible_cost_eur_per_mw': float(schedule.flexible_cost_eur_per_mw.sum()),
        'gross_difference_eur_per_mw': float(schedule.gross_difference_eur_per_mw.sum()),
        'days_changed': int((schedule.best_start_hour != 8).sum()),
    })
    metrics['gross_reduction_pct'] = 100 * metrics['gross_difference_eur_per_mw'] / metrics['baseline_cost_eur_per_mw']
    metrics['break_even_cost_per_changed_day_eur_per_mw'] = metrics['gross_difference_eur_per_mw'] / metrics['days_changed'] if metrics['days_changed'] else 0
    for name, frame in {**frames, 'monthly': monthly}.items():
        frame.to_csv(out / f'{name}.csv', index=False, float_format='%.8f')
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    m = metrics
    summary = f'''# 2025 German electricity: operating flexibility study

**Decision:** Is a controlled pilot worth evaluating for a process that can move its daily operating block?

This is a retrospective portfolio study using public data. It does not describe a real business, customer meter, investment return or achieved operational saving.

## Measured market facts

- {m['quarter_hours']:,.0f} aligned quarter-hour records, representing {m['priced_hours']:,.0f} hours.
- Time-weighted average DE-LU day-ahead price: **€{m['mean_price_eur_mwh']:.2f}/MWh**.
- Negative-price duration: **{m['negative_price_hours']:,.2f} hours**. Negative values are valid market observations.
- Observed range: €{m['min_price_eur_mwh']:.2f} to €{m['max_price_eur_mwh']:.2f}/MWh.
- German wind-plus-solar generation / load (ratio of energy sums): **{m['wind_solar_load_ratio']:.1%}**. This excludes hydro, biomass and other renewables; it is not the total renewable share.

## Explicit scheduling scenario

A hypothetical constant **1 MW** process runs **4 consecutive hours every calendar day**, consuming 4 MWh/day. Baseline: 08:00–12:00 Europe/Berlin. Flexible starts: whole hours from 06:00 through 18:00, finishing by 22:00. The model chooses the lowest-cost block using that delivery day's day-ahead price curve. Equal-cost ties use the earliest start.

Across **{m['eligible_days']} eligible days**:

| Measure | Energy-only scenario |
|---|---:|
| Baseline cost | €{m['baseline_cost_eur_per_mw']:,.2f} |
| Flexible cost | €{m['flexible_cost_eur_per_mw']:,.2f} |
| Gross difference | €{m['gross_difference_eur_per_mw']:,.2f} |
| Gross reduction against baseline | {m['gross_reduction_pct']:.1f}% |
| Days with a different start | {m['days_changed']} |

The gross difference averages **€{m['break_even_cost_per_changed_day_eur_per_mw']:.2f} per changed day**. That is a break-even ceiling for an assumed constant incremental rescheduling cost, before other omitted costs. It is not an operating-cost estimate. Power scales linearly: a 100 kW process has one tenth of these energy-only costs and differences.

## Decision and pilot design

1. First confirm whether a real process can move four continuous hours without violating throughput, staffing, maintenance or customer deadlines.
2. Verify exposure to these prices in the actual contract. Add grid tariffs, taxes, levies, imbalance costs and start/stop costs before any commercial decision.
3. Run a shadow schedule, record the price curve available at the decision time, and compare predicted versus realized total cost on matched operating days.
4. Proceed only if measured net benefit remains positive and operational service levels are maintained.

## Quality and interpretation

UTC is the join key; local dates and hours drive scheduling. The 23-hour and 25-hour daylight-saving days remain intact. Hourly prices before 1 October are applied to their four constituent quarters; subsequent prices retain their native 15-minute resolution. Missing data is never zero-filled or carried through gaps. The build fails if this fixed snapshot has incomplete coverage.

Day-ahead prices would normally be available before the delivery day, but this historical API download does not preserve original publication timestamps or revisions. Therefore the schedule is a retrospective price-curve benchmark, **not a verified live backtest**. Actual generation/load is used only for descriptive analysis, never to choose the schedule. National aggregate generation does not establish the electricity mix consumed by a particular site. No causal or carbon-emissions claim is made.

Source: Energy-Charts.info; price data credited by API to Bundesnetzagentur / SMARD.de. CC BY 4.0. See [provenance](../data/provenance.json), [data notes](../data/README.md) and [methodology](../docs/methodology.md).
'''
    (out / 'executive_summary.md').write_text(summary)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), facecolor='#f5f7fa', constrained_layout=True)
    fig.suptitle('GERMAN ENERGY OPERATIONS  /  2025\nMarket evidence and a clearly defined flexibility scenario', fontsize=18, fontweight='bold', ha='left', x=0.04)
    daily = frames['daily']
    axes[0,0].plot(daily.local_date, daily.mean_price_eur_mwh, color='#087f8c', linewidth=1)
    axes[0,0].axhline(0, color='#aaa', linewidth=.8)
    axes[0,0].set(title='Daily average wholesale price', ylabel='EUR / MWh')
    labels = monthly.month.str[-2:]
    axes[0,1].bar(labels, monthly.negative_price_hours, color='#087f8c')
    axes[0,1].set(title=f'Negative prices: {m["negative_price_hours"]:,.2f} hours', ylabel='Hours', xlabel='Month')
    axes[1,0].plot(labels, monthly.baseline_cost_eur_per_mw, label='Fixed 08:00–12:00', color='#64748b', marker='o')
    axes[1,0].plot(labels, monthly.flexible_cost_eur_per_mw, label='Flexible 4-hour block', color='#e57c32', marker='o')
    axes[1,0].set(title='Hypothetical 1 MW process • energy only', ylabel='Monthly EUR', xlabel='Month')
    axes[1,0].legend(frameon=False)
    hours = schedule.best_start_hour.value_counts().sort_index()
    axes[1,1].bar(hours.index, hours.values, color='#e57c32')
    axes[1,1].set(title='Lowest-cost start in the retrospective scenario', ylabel='Days', xlabel='Start hour • Europe/Berlin', xticks=range(6,19,2))
    for ax in axes.flat:
        ax.grid(axis='y', alpha=.15)
        ax.set_axisbelow(True)
    fig.savefig(out / 'overview.png', dpi=150)
    plt.close(fig)
    print(json.dumps(metrics, indent=2))
