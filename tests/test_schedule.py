"""Execute the actual dbt schedule SQL against controlled synthetic price curves."""
from pathlib import Path
import duckdb
import pandas as pd
import pytest

SQL=(Path(__file__).parents[1]/'dbt/models/marts/mart_schedule.sql').read_text().replace("{{ ref('fct_market_quarter') }}",'fixture')

def run(prices):
    times=pd.date_range('2025-01-02T00:00Z',periods=96,freq='15min')
    f=pd.DataFrame({'ts_utc':times,'local_date':times.tz_convert('Europe/Berlin').date,
                    'local_hour':times.tz_convert('Europe/Berlin').hour,'price_eur_mwh':prices})
    f['cost_eur_per_mw']=f.price_eur_mwh*.25
    with duckdb.connect() as c:
        c.register('fixture',f)
        return c.sql(SQL).df()


def test_lowest_contiguous_block_and_exact_units():
    # Local noon through 16:00 has a negative price, all other quarters cost 100.
    prices=[-20 if 11<=i/4<15 else 100 for i in range(96)]
    r=run(prices).iloc[0]
    assert r.best_start_hour==12
    assert r.flexible_cost_eur_per_mw==-80
    assert r.baseline_cost_eur_per_mw==400
    assert r.gross_difference_eur_per_mw==480


def test_tie_uses_earliest_start_and_zero_saving():
    r=run([10]*96).iloc[0]
    assert r.best_start_hour==6 and r.gross_difference_eur_per_mw==0


def test_gap_excludes_day_instead_of_creating_artificial_saving():
    prices=[10.0]*96;prices[40]=None
    assert run(prices).empty
