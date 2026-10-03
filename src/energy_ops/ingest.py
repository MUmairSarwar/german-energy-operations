"""Reproducible, bounded public API ingestion; no credentials needed."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URLS = {
    'price': 'https://api.energy-charts.info/price?bzn=DE-LU&start=2025-01-01&end=2025-12-31',
    'power': 'https://api.energy-charts.info/public_power?country=de&start=2025-01-01&end=2025-12-31',
}
SERIES = {'Load': 'load_mw', 'Solar': 'solar_mw', 'Wind onshore': 'wind_onshore_mw', 'Wind offshore': 'wind_offshore_mw'}

def create_snapshot(download: bool = False) -> None:
    raw_dir = ROOT / 'data/raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    snapshot, provenance = {}, {}
    for name, url in URLS.items():
        path = raw_dir / f'{name}_2025.json'
        if download or not path.exists():
            with urllib.request.urlopen(url, timeout=90) as response:
                payload = response.read()
            # Parse before committing to cache; HTTP errors are intentionally not hidden.
            json.loads(payload)
            path.write_bytes(payload)
        raw = path.read_bytes()
        data = json.loads(raw)
        if name == 'price':
            snapshot[name] = data
        else:
            snapshot[name] = {
                'unix_seconds': data['unix_seconds'],
                'production_types': [s for s in data['production_types'] if s['name'] in SERIES],
            }
        provenance[name] = {
            'url': url, 'sha256_original_response': hashlib.sha256(raw).hexdigest(),
            'license': data.get('license_info', 'CC BY 4.0; Energy-Charts.info (API default)'),
            'source_rows': len(data['unix_seconds']),
        }
    encoded = json.dumps(snapshot, separators=(',', ':'), allow_nan=False).encode()
    compressed = gzip.compress(encoded, mtime=0)
    (ROOT / 'data/snapshot_2025.json.gz').write_bytes(compressed)
    provenance.update({
        'snapshot_created_utc': datetime.now(timezone.utc).isoformat(),
        'snapshot_sha256': hashlib.sha256(compressed).hexdigest(),
        'scope': '2025 Europe/Berlin; DE-LU prices and German generation/load',
        'transformation': 'Price response unchanged; power response restricted to Load, Solar, Wind onshore and Wind offshore.',
    })
    (ROOT / 'data/provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh', action='store_true', help='Replace cached API data and snapshot')
    args = parser.parse_args()
    create_snapshot(args.refresh)
