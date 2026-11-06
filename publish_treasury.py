"""Publish a truthful daily Treasury evidence snapshot for static hosting.

Run on an internet-connected host. Failure leaves prior data untouched; the
published page labels the data's observation date and retrieval timestamp.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from treasury_xml import collect_month, official_url, parse_xml
from evidence_store import store_evidence
from history_archive import archive_snapshot
import urllib.request


def build_snapshot(raw, source_url, captured_at=None):
    captured_at = captured_at or datetime.now(timezone.utc)
    evidence = parse_xml(raw, captured_at=captured_at)
    evidence['source_url'] = source_url
    last = evidence['observations'][-1]
    return {
        'source': evidence['source'],
        'dataset': evidence['dataset'],
        'source_url': source_url,
        'retrieved_at_utc': evidence['retrieved_at_utc'],
        'observation_date': last['observation_date'],
        'yields_percent': last['yield_percent'],
        'observation_count': len(evidence['observations']),
        'source_file_sha256': evidence['source_file_sha256'],
        'publication_time_verified': False,
        'intraday_quote': False,
        'research_ready': False,
        'live_intraday_market_data_verified': False,
        'note': 'Official daily yield curve observation; not an intraday futures feed or trade signal.'
    }


def run(out='docs/treasury.json', db='easymoney_evidence.sqlite3', now=None, opener=None, history='docs/history'):
    now = now or datetime.now(timezone.utc)
    month = now.strftime('%Y%m')
    url = official_url(month)
    request = urllib.request.Request(url, headers={'User-Agent': 'EasyMoneyResearchCollector/0.7'})
    with (opener or urllib.request.urlopen)(request, timeout=25) as response:
        raw = response.read(10_000_001)
    if len(raw) > 10_000_000:
        raise ValueError('Source response exceeded 10 MB')
    snapshot = build_snapshot(raw, url, captured_at=now)
    full = parse_xml(raw, captured_at=now)
    full['source_url'] = url
    store_evidence(db, full)
    archive_snapshot(snapshot, history)
    destination = Path(out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
    temporary.replace(destination)
    return snapshot

if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
