import copy
import pandas as pd
import pytest
from energy_ops.normalize import build_spine, price_quarters, power_quarters, timestamps


def price(times, values):
    return {'unix_seconds':[int(pd.Timestamp(t).timestamp()) for t in times], 'price':values,'unit':'EUR / MWh'}


def test_hourly_expansion_preserves_negative_price_and_cost():
    f=price_quarters(price(['2025-01-01T00:00Z'],[-20]))
    assert len(f)==4
    assert f.price_eur_mwh.sum()*.25 == -20


def test_native_quarters_are_not_expanded():
    f=price_quarters(price(['2025-10-01T00:00Z','2025-10-01T00:15Z'],[10,20]))
    assert len(f)==2
    assert f.price_eur_mwh.sum()*.25 == 7.5


def test_transition_has_no_overlap_or_gap():
    f=price_quarters(price(['2025-09-30T21:00Z','2025-09-30T22:00Z'],[5,6]))
    assert len(f)==5 and f.ts_utc.diff().dropna().eq(pd.Timedelta(minutes=15)).all()


def test_missing_hour_is_not_forward_filled():
    f=price_quarters(price(['2025-01-01T00:00Z','2025-01-01T02:00Z'],[10,30]))
    assert len(f)==8 and not f.ts_utc.dt.hour.eq(1).any()


def test_null_price_is_not_zero():
    f=price_quarters(price(['2025-01-01T00:00Z'],[None]))
    assert f.price_eur_mwh.isna().all()


@pytest.mark.parametrize('times,values',[
    (['2025-01-01T00:00Z']*2,[1,2]),
    (['2025-01-01T01:00Z','2025-01-01T00:00Z'],[1,2]),
    (['2025-01-01T00:05Z'],[1]),
    (['2025-01-01T00:15Z'],[1]),
    (['2025-01-01T00:00Z'],[float('inf')]),
    (['2025-01-01T00:00Z'],[]),
])
def test_bad_price_contract_rejected(times,values):
    with pytest.raises(ValueError): price_quarters(price(times,values))


def test_wrong_unit_rejected():
    p=price(['2025-01-01T00:00Z'],[1]);p['unit']='EUR/kWh'
    with pytest.raises(ValueError): price_quarters(p)


def test_dst_spine_retains_physical_intervals():
    f=build_spine(); hours=f.groupby('local_date').size()/4
    assert hours.loc[pd.Timestamp('2025-03-30').date()]==23
    assert hours.loc[pd.Timestamp('2025-10-26').date()]==25
    assert len(f)==35040 and f.ts_utc.is_unique
    local=f[f.local_date==pd.Timestamp('2025-10-26').date()]
    assert len(local[local.local_hour==2])==8


def power():
    return {'unix_seconds':[1735686000], 'production_types':[
        {'name':n,'data':[v]} for n,v in [('Load',100),('Solar',0),('Wind onshore',20),('Wind offshore',5)]]}


def test_power_mw_and_null_preservation():
    p=power();p['production_types'][1]['data']=[None]
    f=power_quarters(p)
    assert f.load_mw.iloc[0]==100 and pd.isna(f.solar_mw.iloc[0])


@pytest.mark.parametrize('change',['missing','length','negative','zero_load','duplicate'])
def test_power_contract_rejects_invalid(change):
    p=power()
    if change=='missing': p['production_types'].pop()
    if change=='length': p['production_types'][0]['data']=[]
    if change=='negative': p['production_types'][1]['data']=[-1]
    if change=='zero_load': p['production_types'][0]['data']=[0]
    if change=='duplicate': p['production_types'].append(copy.deepcopy(p['production_types'][0]))
    with pytest.raises(ValueError):power_quarters(p)
