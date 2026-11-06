"""Freshness/coverage report for EasyMoney FRED evidence snapshots.

Freshness is a property of a *specific observation* and use-case. This tool
reports ages; it never asserts that a daily/monthly series is a live quote.
"""
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

EXPECTED_FREQUENCY = {
    'growth_real_gdp': 'quarterly',
    'inflation_cpi_index': 'monthly',
    'rates_ten_year_yield': 'daily',
    'credit_high_yield_oas': 'daily',
    'liquidity_fed_assets': 'weekly',
}

def evaluate(snapshot, now=None):
    now = now or datetime.now(timezone.utc)
    retrieved = datetime.fromisoformat(snapshot['retrieved_at_utc'].replace('Z', '+00:00'))
    if retrieved.tzinfo is None:
        raise ValueError('retrieved_at_utc must include timezone')
    report = {'checked_at_utc': now.isoformat(), 'retrieved_at_utc': retrieved.isoformat(),
              'retrieval_age_seconds': max(0, int((now-retrieved).total_seconds())),
              'series': {}, 'live_intraday_market_data_verified': False,
              'research_ready': False}
    for name, freq in EXPECTED_FREQUENCY.items():
        record = snapshot.get('series', {}).get(name, {})
        observations = record.get('observations') or []
        valid = [o for o in observations if o.get('observation_date') and o.get('value') is not None]
        latest = max(valid, key=lambda o: o['observation_date']) if valid else None
        age = (now.date()-date.fromisoformat(latest['observation_date'])).days if latest else None
        report['series'][name] = {
            'frequency_expected': freq, 'source_status': record.get('status', 'missing'),
            'latest_observation_date': latest['observation_date'] if latest else None,
            'observation_age_days': age, 'exact_publication_time_verified': False,
            'intraday_quote': False,
            'usable_for_intraday_quote': False,
            'note': 'Age is not latency. Validate publication calendar and revisions before point-in-time analysis.'
        }
    return report

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python freshness.py easymoney_macro_evidence_YYYY-MM-DD.json')
    source = Path(sys.argv[1]); output = source.with_name(source.stem+'_freshness.json')
    output.write_text(json.dumps(evaluate(json.loads(source.read_text())), indent=2))
    print(f'Wrote {output}')
