"""Read-only ingestion of official US Treasury daily par yield CSV exports.

No trading decisions. No real-time quote claims. Input CSV is supplied by the operator
or an independently authorized retrieval process. This module never guesses publication time.
"""
import csv
import hashlib
import io
import json
import sys
from datetime import datetime, date, timezone
from pathlib import Path

TENORS = {'1 Mo':'1m','3 Mo':'3m','6 Mo':'6m','1 Yr':'1y','2 Yr':'2y',
          '3 Yr':'3y','5 Yr':'5y','7 Yr':'7y','10 Yr':'10y','20 Yr':'20y','30 Yr':'30y'}

def workbook_yields(values):
    """Expose workbook tenor names alongside the collector's compact keys."""
    if not isinstance(values, dict):
        return {}
    mapped = dict(values)
    for key in TENORS.values():
        term = key[:-1] + ('-year' if key.endswith('y') else '-month')
        if key in values:
            mapped.setdefault(term, values[key])
    return mapped


def parse_treasury_csv(raw, captured_at=None):
    captured_at = captured_at or datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        raise ValueError('Capture timestamp must be timezone-aware')
    text = raw.decode('utf-8-sig') if isinstance(raw, bytes) else raw
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or 'Date' not in reader.fieldnames or '10 Yr' not in reader.fieldnames:
        raise ValueError('Expected Treasury CSV headers Date and 10 Yr')
    records = []
    seen = set()
    for row in reader:
        date_string = (row.get('Date') or '').strip()
        if not date_string:
            continue
        try:
            observation_date = datetime.strptime(date_string, '%m/%d/%Y').date()
        except ValueError as exc:
            raise ValueError(f'Invalid Treasury date: {date_string}') from exc
        if observation_date in seen:
            raise ValueError(f'Duplicate Treasury observation date: {observation_date}')
        if observation_date > captured_at.date():
            raise ValueError(f'Future observation date: {observation_date}')
        seen.add(observation_date)
        yields = {}
        for header, key in TENORS.items():
            raw_value = (row.get(header) or '').strip()
            if not raw_value or raw_value.upper() in ('N/A','ND'):
                yields[key] = None
            else:
                try:
                    val = float(raw_value)
                except ValueError as exc:
                    raise ValueError(f'Invalid yield {header} for {observation_date}') from exc
                if not -5 <= val <= 30:
                    raise ValueError(f'Implausible yield {header} for {observation_date}')
                yields[key] = val
        records.append({'observation_date':observation_date.isoformat(), 'yield_percent':yields})
    if not records:
        raise ValueError('Treasury CSV has no observations')
    records.sort(key=lambda r:r['observation_date'])
    return {'source':'US Treasury', 'dataset':'Daily Treasury Par Yield Curve Rates',
            'retrieved_at_utc':captured_at.astimezone(timezone.utc).isoformat(),
            'source_file_sha256':hashlib.sha256(raw if isinstance(raw,bytes) else raw.encode()).hexdigest(),
            'source_publication_time_verified':False,
            'intraday_quote':False,
            'status':'historical_daily_evidence_only',
            'latest_observation_date':records[-1]['observation_date'],
            'observations':records,
            'warning':'Daily official yield observations are not live tradable Treasury futures quotes. Exact release time not verified.'}

def main():
    if len(sys.argv)!=3:
        sys.exit('Usage: python treasury_yields.py input_treasury.csv output.json')
    raw = Path(sys.argv[1]).read_bytes()
    data = parse_treasury_csv(raw)
    Path(sys.argv[2]).write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(f"Imported {len(data['observations'])} official daily yield observations; latest {data['latest_observation_date']}")

if __name__=='__main__':
    main()
