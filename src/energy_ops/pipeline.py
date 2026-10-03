"""Build local warehouse, execute dbt tests, export recruiter-readable results."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import duckdb
from .ingest import ROOT
from .normalize import START, END, build_spine, price_quarters, power_quarters


def run() -> None:
    snapshot = ROOT / 'data/snapshot_2025.json.gz'
    provenance = json.loads((ROOT / 'data/provenance.json').read_text())
    payload = snapshot.read_bytes()
    if hashlib.sha256(payload).hexdigest() != provenance['snapshot_sha256']:
        raise ValueError('Snapshot checksum mismatch; refresh explicitly to accept a new source version')
    data = json.loads(gzip.decompress(payload))
    prices, power, spine = price_quarters(data['price']), power_quarters(data['power']), build_spine()
    for name, frame in [('prices', prices), ('power', power)]:
        if not frame.ts_utc.between(START, END, inclusive='left').all():
            raise ValueError(f'{name}: out-of-scope timestamp')
    warehouse = ROOT / 'warehouse'
    warehouse.mkdir(exist_ok=True)
    path = warehouse / 'energy.duckdb'
    with duckdb.connect(str(path)) as con:
        con.execute('create schema if not exists raw')
        for name, frame in [('prices', prices), ('power', power), ('time_spine', spine)]:
            con.register('input_frame', frame)
            con.execute(f'create or replace table raw.{name} as select * from input_frame')
            con.unregister('input_frame')
    env = dict(os.environ, ENERGY_DB_PATH=str(path), DBT_SEND_ANONYMOUS_USAGE_STATS='false')
    dbt = str(Path(sys.executable).parent / ('dbt.exe' if os.name == 'nt' else 'dbt'))
    common = ['--project-dir', str(ROOT / 'dbt'), '--profiles-dir', str(ROOT / 'dbt')]
    subprocess.run([dbt, 'build', *common], env=env, check=True)
    subprocess.run([dbt, 'docs', 'generate', *common], env=env, check=True)
    from .report import export_reports
    export_reports(path)

if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
