"""EasyMoney public-data ingestion prototype (research evidence only).

Requires a free FRED API key via FRED_API_KEY environment variable.
Does not score regimes, classify trades, or submit orders.
"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# These are illustrative source candidates, NOT a complete macro model.
SERIES = {
    'growth_real_gdp': 'GDPC1',
    'inflation_cpi_index': 'CPIAUCSL',
    'rates_ten_year_yield': 'DGS10',
    'credit_high_yield_oas': 'BAMLH0A0HYM2',
    'liquidity_fed_assets': 'WALCL',
}
BASE = 'https://api.stlouisfed.org/fred/series/observations'

def parse_observations(payload):
    if 'observations' not in payload or not isinstance(payload['observations'], list):
        raise ValueError('FRED response missing observations list')
    out = []
    for item in payload['observations']:
        raw = item.get('value')
        if raw in (None, '.', ''):
            continue
        out.append({
            'observation_date': item['date'],
            'value': float(raw),
            'realtime_start': item.get('realtime_start'),
            'realtime_end': item.get('realtime_end'),
        })
    return out

def fetch_series(series_id, api_key, as_of, timeout=20):
    # as_of is a historical-vintage boundary, not a verified publication timestamp.
    params = {
        'series_id': series_id, 'api_key': api_key, 'file_type': 'json',
        'realtime_start': as_of, 'realtime_end': as_of,
        'sort_order': 'desc', 'limit': '20',
    }
    url = BASE + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.load(response)
    if 'error_message' in payload:
        raise RuntimeError(payload['error_message'])
    return parse_observations(payload)

def build_snapshot(api_key, as_of):
    datetime.strptime(as_of, '%Y-%m-%d')
    captured = datetime.now(timezone.utc).isoformat()
    output = {'as_of_date': as_of, 'retrieved_at_utc': captured,
              'status': 'source_evidence_only_no_regime_score', 'series': {}}
    for label, series_id in SERIES.items():
        try:
            obs = fetch_series(series_id, api_key, as_of)
            output['series'][label] = {
                'source': 'FRED', 'series_id': series_id,
                'endpoint': BASE, 'observations': obs,
                'status': 'ok' if obs else 'missing',
                'warning': 'Vintage date is not exact intraday release time; validate original publication before replay.'
            }
        except Exception as exc:
            output['series'][label] = {'source': 'FRED', 'series_id': series_id,
                                       'status': 'unavailable', 'error': str(exc)}
    return output

def main():
    key = os.environ.get('FRED_API_KEY')
    if not key:
        sys.exit('Missing FRED_API_KEY. Register for a free key at https://fred.stlouisfed.org/docs/api/api_key.html')
    as_of = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
    output = build_snapshot(key, as_of)
    path = Path('easymoney_macro_evidence_' + as_of + '.json')
    path.write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(f'Wrote {path}; sources retrieved: ' + str(sum(s['status']=='ok' for s in output['series'].values())) + '/5')

if __name__ == '__main__':
    main()
