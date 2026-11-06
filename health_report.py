"""Read-only evidence health report. No market recommendations or invented freshness."""
import argparse
import json
from datetime import datetime, date, timezone
from pathlib import Path
from evidence_store import list_evidence


def evaluate_archive(db_path, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Current time must be timezone-aware')
    entries = list_evidence(db_path)
    sources = {}
    for item in entries:
        key = (item['source'], item['dataset'])
        if key in sources:
            continue
        captured = datetime.fromisoformat(item['captured_at_utc'].replace('Z', '+00:00'))
        if captured.tzinfo is None or captured > now:
            status = 'INVALID_CAPTURE_TIME'
            age = None
        else:
            age = int((now-captured).total_seconds())
            status = 'ARCHIVED_NOT_LIVE_VERIFIED'
        observed = item['observed_through']
        try:
            observation_age_days = (now.date() - date.fromisoformat(observed)).days if observed else None
        except ValueError:
            observation_age_days = None
            status = 'INVALID_OBSERVATION_DATE'
        sources[key] = {
            'source': item['source'], 'dataset': item['dataset'],
            'last_retrieved_at_utc': item['captured_at_utc'],
            'retrieval_age_seconds': age, 'latest_observation_date': observed,
            'observation_age_days': observation_age_days, 'status': status,
            'publication_time_verified': False, 'intraday_quote': False,
        }
    return {
        'checked_at_utc': now.astimezone(timezone.utc).isoformat(),
        'archive_exists': Path(db_path).is_file(),
        'datasets': list(sources.values()),
        'evidence_record_count': len(entries),
        'research_ready': False,
        'live_intraday_market_data_verified': False,
        'warning': 'Archive receipt time does not establish original publication time, live availability, or trading readiness.',
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='easymoney_evidence.sqlite3')
    args = parser.parse_args()
    print(json.dumps(evaluate_archive(args.db), indent=2))
