"""Explicit interval contracts, UTC joins, and missingness-preserving normalization."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .ingest import SERIES

START = pd.Timestamp('2025-01-01', tz='Europe/Berlin').tz_convert('UTC')
END = pd.Timestamp('2026-01-01', tz='Europe/Berlin').tz_convert('UTC')
TRANSITION = pd.Timestamp('2025-10-01', tz='Europe/Berlin').tz_convert('UTC')


def timestamps(values: list[int]) -> pd.DatetimeIndex:
    result = pd.to_datetime(values, unit='s', utc=True)
    if not len(result) or result.has_duplicates or not result.is_monotonic_increasing:
        raise ValueError('Timestamps must be non-empty, unique and increasing')
    if ((result.asi8 // 10**9) % 900 != 0).any():
        raise ValueError('Timestamps must align to quarter-hour boundaries')
    return result


def price_quarters(data: dict) -> pd.DataFrame:
    if data.get('unit') != 'EUR / MWh':
        raise ValueError('Unexpected price unit')
    idx = timestamps(data['unix_seconds'])
    if len(idx) != len(data['price']):
        raise ValueError('Price timestamp/value length mismatch')
    prices = pd.to_numeric(pd.Series(data['price']), errors='raise')
    if np.isinf(prices.dropna().to_numpy(dtype=float)).any():
        raise ValueError('Infinite price')
    rows = []
    for t, value in zip(idx, prices):
        # Fixed market contract, NOT next-row difference: missing intervals stay missing.
        duration = 60 if t < TRANSITION else 15
        if duration == 60 and t.minute != 0:
            raise ValueError('Pre-transition price must begin on the hour')
        for minute in range(0, duration, 15):
            rows.append((t + pd.Timedelta(minutes=minute), value, duration))
    result = pd.DataFrame(rows, columns=['ts_utc', 'price_eur_mwh', 'source_interval_minutes'])
    if result.ts_utc.duplicated().any():
        raise ValueError('Overlapping price intervals')
    return result


def power_quarters(data: dict) -> pd.DataFrame:
    idx = timestamps(data['unix_seconds'])
    columns = {'ts_utc': idx}
    names = [s['name'] for s in data['production_types']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate power series')
    for source, target in SERIES.items():
        found = [s for s in data['production_types'] if s['name'] == source]
        if len(found) != 1 or len(found[0]['data']) != len(idx):
            raise ValueError(f'Missing or misaligned power series: {source}')
        values = pd.to_numeric(pd.Series(found[0]['data']), errors='raise')
        if np.isinf(values.dropna().to_numpy(dtype=float)).any():
            raise ValueError('Infinite power value')
        if (values.dropna() < 0).any():
            raise ValueError(f'Negative physical quantity: {source}')
        if source == 'Load' and (values.dropna() <= 0).any():
            raise ValueError('Load must be positive')
        columns[target] = values.to_numpy()
    return pd.DataFrame(columns)


def build_spine(start=START, end=END) -> pd.DataFrame:
    idx = pd.date_range(start, end, inclusive='left', freq='15min')
    local = idx.tz_convert('Europe/Berlin')
    return pd.DataFrame({
        'ts_utc': idx, 'local_date': local.date, 'local_hour': local.hour,
        'month': local.strftime('%Y-%m'), 'weekday': local.dayofweek,
        'local_timestamp': local.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'interval_hours': 0.25,
    })
