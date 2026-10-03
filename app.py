"""Interactive project dashboard. Run the tested pipeline before launch."""
from pathlib import Path
import json
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title='German Energy Operations', page_icon='⚡', layout='wide')
st.title('German Energy Operations')
st.caption('2025 • DE-LU wholesale prices + German generation/load • Independent portfolio project')
st.info('Historical simulation, not achieved savings. Wholesale energy only; taxes, network charges and operating constraints are excluded.')
path = ROOT / 'warehouse/energy.duckdb'
if not path.exists():
    st.warning('Run `python -m energy_ops.pipeline` first to build and validate the warehouse.')
    st.stop()

@st.cache_data
def load_data(modified):
    with duckdb.connect(str(path), read_only=True) as con:
        return [con.sql(f'select * from {table} order by 1').df() for table in ['mart_daily','mart_schedule','mart_quality','fct_market_quarter']]

daily, schedule, quality, quarter = load_data(path.stat().st_mtime_ns)
months = sorted(daily.month.unique())
selected = st.sidebar.multiselect('Months', months, default=months)
capacity = st.sidebar.slider('Hypothetical process power (MW)', 0.1, 5.0, 1.0, 0.1)
shift_cost = st.sidebar.number_input('Extra cost per changed day (EUR)', min_value=0.0, value=0.0, step=10.0)
st.sidebar.caption('4 uninterrupted hours/day; baseline 08:00–12:00. Allowed starts 06:00–18:00. All times Europe/Berlin. These inputs are scenario assumptions, not measured site data.')
if not selected:
    st.warning('Choose at least one month.')
    st.stop()
d = daily[daily.month.isin(selected)]
s = schedule[schedule.local_date.isin(d.local_date)].copy()
q = quarter[quarter.month.isin(selected)]
gross = s.gross_difference_eur_per_mw.sum()*capacity
changed = int((s.best_start_hour != 8).sum())
cols = st.columns(4)
cols[0].metric('Average wholesale price', f'€{q.price_eur_mwh.mean():.2f}/MWh')
cols[1].metric('Negative-price duration', f'{q.negative_price.sum()*.25:,.2f} h')
cols[2].metric('Gross scenario difference', f'€{gross:,.0f}')
cols[3].metric('After assumed shift cost', f'€{gross-changed*shift_cost:,.0f}')
st.caption(f'{len(q):,} expected quarter-hours • {len(s)} eligible operating days • {changed} changed starts. The shift-cost adjustment evaluates the gross-optimal schedule; it does not re-optimize it.')
market, flexibility, checks, methods = st.tabs(['Market overview','Operating flexibility','Data quality','Method & sources'])
with market:
    fig = px.line(d, x='local_date', y='mean_price_eur_mwh', labels={'local_date':'Local date','mean_price_eur_mwh':'EUR / MWh'}, title='Daily average day-ahead price', color_discrete_sequence=['#087f8c'])
    st.plotly_chart(fig, width='stretch')
    c1,c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(d.groupby('month',as_index=False).negative_price_hours.sum(), x='month', y='negative_price_hours', labels={'negative_price_hours':'Hours'}, title='Duration below zero'),width='stretch')
    with c2:
        display = d.copy(); display['wind_solar_pct'] = 100*display.wind_solar_load_ratio
        st.plotly_chart(px.line(display,x='local_date',y='wind_solar_pct',labels={'wind_solar_pct':'Wind + solar / load (%)','local_date':'Local date'},title='Wind and solar relative to load'),width='stretch')
    st.caption('Wind + solar / load is not total renewable share and is not a site-specific electricity mix.')
with flexibility:
    totals = s.copy()
    for col in ['baseline_cost_eur_per_mw','flexible_cost_eur_per_mw']:
        totals[col] = totals[col]*capacity
    st.plotly_chart(px.line(totals, x='local_date', y=['baseline_cost_eur_per_mw','flexible_cost_eur_per_mw'], labels={'value':'Daily energy-only EUR','local_date':'Local date','variable':'Schedule'},title='Fixed versus flexible 4-hour operating block'),width='stretch')
    chosen = st.selectbox('Inspect an operating day', s.local_date.dt.strftime('%Y-%m-%d').tolist())
    day = q[q.local_date == pd.Timestamp(chosen)].copy()
    optimum = int(s.loc[s.local_date == pd.Timestamp(chosen),'best_start_hour'].iloc[0])
    day['period'] = day.local_hour.map(lambda h: 'Selected block' if optimum <= h < optimum+4 else 'Other hours')
    day['local_label'] = day.local_timestamp.str[11:16] + ' ' + day.local_timestamp.str[-5:]
    st.plotly_chart(px.bar(day,x='local_label',y='price_eur_mwh',color='period',labels={'local_label':'Local interval start (UTC offset)','price_eur_mwh':'EUR / MWh'},title=f'Selected start: {optimum:02d}:00 • {chosen}'),width='stretch')
    st.download_button('Download selected schedule (per 1 MW)', s.to_csv(index=False), 'schedule.csv','text/csv')
with checks:
    st.dataframe(quality[quality.month.isin(selected)],width='stretch',hide_index=True)
    st.caption('Negative prices and wind/solar above load are market signals, not failures. Missing price/power data fails the fixed-snapshot build. Duplicates, overlaps and wrong units fail ingestion.')
    st.write('Daylight-saving audit')
    st.dataframe(daily[daily.expected_hours != 24][['local_date','expected_hours','priced_hours']],hide_index=True)
with methods:
    st.markdown((ROOT / 'docs/methodology.md').read_text())
    st.json(json.loads((ROOT / 'data/provenance.json').read_text()))
st.caption('Muhammad Umair Sarwar • Public data: Energy-Charts.info; prices: Bundesnetzagentur / SMARD.de • CC BY 4.0')
