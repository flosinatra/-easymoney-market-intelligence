"""Retrieve a configured official Treasury CSV, validate, and archive it.

Requires the operator to supply an official CSV endpoint URL; does not assume
publication time or claim intraday futures pricing. No automatic schedule.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path
from treasury_yields import parse_treasury_csv
from evidence_store import store_evidence

def collect(url, db_path, timeout=20, opener=None):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('home.treasury.gov', 'www.treasury.gov', 'treasury.gov'):
        raise ValueError('URL must be HTTPS on an official US Treasury host')
    request = urllib.request.Request(url, headers={'User-Agent':'EasyMoneyResearchCollector/0.4'})
    with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
        raw = response.read(10_000_001)
    if len(raw) > 10_000_000:
        raise ValueError('Source response exceeded 10 MB')
    payload = parse_treasury_csv(raw)
    payload['source_url'] = url
    archive = store_evidence(db_path, payload)
    return {'source':'US Treasury', 'latest_observation_date':payload['latest_observation_date'],
            'observation_count':len(payload['observations']), 'archive':archive,
            'live_intraday_market_data_verified':False, 'research_ready':False,
            'publication_time_verified':False}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--url', required=True, help='Verified official Treasury CSV export URL')
    p.add_argument('--db', default='easymoney_evidence.sqlite3')
    args = p.parse_args()
    print(json.dumps(collect(args.url,args.db),indent=2))
