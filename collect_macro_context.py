"""Download public FRED CSV observations for context; never claim release-time verification.

FRED CSV dates are observation dates, not dates the data became public. These
observations are intentionally excluded from scored Weekly Regime evidence.
"""
import csv
import io
import os
import json
import re
import urllib.request
from urllib.parse import urlencode
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from collection_health import receipt, write_json_atomic

SERIES = {
    'Growth': ('INDPRO', 'Industrial Production Index', 'index'),
    'Inflation': ('CPIAUCSL', 'Consumer Price Index for All Urban Consumers', 'index'),
    'Credit': ('BAMLH0A0HYM2', 'ICE BofA US High Yield Option-Adjusted Spread', 'percentage points'),
    'Liquidity': ('WALCL', 'Federal Reserve Total Assets', 'millions of USD'),
}
URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?cosd={}&id={}'

def parse_series(raw, series_id, as_of):
    rows = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    fields = rows.fieldnames or []
    date_column = next((field for field in ('observation_date', 'DATE') if field in fields), None)
    if date_column is None or series_id not in fields:
        raise ValueError('Unexpected FRED CSV schema')
    observations=[]
    for row in rows:
        try:
            day=date.fromisoformat(row[date_column])
            value=float(row[series_id])
            if day <= as_of and abs(value) < 1e12 and value == value:
                observations.append((day,value))
        except (TypeError,ValueError,KeyError):
            continue
    if not observations:
        raise ValueError('No usable historical observations')
    return max(observations,key=lambda r:r[0])

def read_fred_api(sid, as_of, opener, api_key):
    params = {'series_id': sid, 'file_type': 'json', 'sort_order': 'desc',
              'observation_end': as_of.isoformat(), 'limit': 24}
    public_url = 'https://api.stlouisfed.org/fred/series/observations?' + urlencode(params)
    request = urllib.request.Request(public_url + '&' + urlencode({'api_key': api_key}))
    # Keep the credential out of source links, saved exceptions and public receipts.
    try:
        with opener(request, timeout=25) as response:
            raw = response.read(200_001)
        if len(raw) > 200_000:
            raise ValueError('Oversized response')
        rows = json.loads(raw)['observations']
        observations = []
        for row in rows:
            if row.get('value') == '.':
                continue
            day = date.fromisoformat(row['date'])
            value = float(row['value'])
            if day <= as_of and abs(value) < 1e12:
                observations.append((day, value))
        day, value = max(observations)
        return day, value, public_url
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise ValueError('FRED API request failed (' + type(exc).__name__ + ')') from None


def read_series(sid, now, opener):
    day = now.date()
    start = (day - timedelta(days=366)).isoformat()
    vintage = now.astimezone(ZoneInfo('America/Chicago')).date()
    archive_url = ('https://alfred.stlouisfed.org/graph/alfredgraph.csv'
                   f'?cosd={start}&vintage_date={vintage.isoformat()}&id={sid}')
    page_url = f'https://fred.stlouisfed.org/series/{sid}'
    failures = []
    api_key = os.getenv('FRED_API_KEY')
    if api_key:
        try:
            return read_fred_api(sid, day, opener, api_key)
        except ValueError as exc:
            failures.append(str(exc))
    sources = [('FRED CSV', URL.format(start, sid), sid),
               ('ALFRED vintage CSV', archive_url, f'{sid}_{vintage:%Y%m%d}'),
               ('FRED series page', page_url, None)]
    for name, url, column in sources:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'EasyMoneyResearchCollector/0.25'})
            with opener(req, timeout=25) as response:
                raw = response.read(3_000_001)
            if len(raw) > 3_000_000:
                raise ValueError('Response too large')
            if column:
                observed, value = parse_series(raw, column, day)
            else:
                observed, value = parse_series_page(raw, url, day)
            return observed, value, url
        except (OSError, ValueError) as exc:
            failures.append(f'{name}: {exc}')
    raise ValueError(' | '.join(failures))


def parse_series_page(raw, expected_url, as_of):
    page = raw.decode('utf-8')
    if f'<link rel="canonical" href="{expected_url}">' not in page:
        raise ValueError('FRED series identity mismatch')
    period = re.search(r'<meta name="dcterms:PeriodOfTime" content="start:[0-9-]+; end:([0-9-]+);">', page)
    quotes = re.findall(r'([^<>]+):\s*<span class="series-meta-observation-value">([0-9.,-]+)</span>', page)
    if not period or not quotes:
        raise ValueError('Missing FRED observation')
    observed = date.fromisoformat(period.group(1))
    values = {float(number.replace(',', '')) for _, number in quotes}
    labels = {label.strip() for label, _ in quotes}
    dates = {observed.strftime('%b %Y'), observed.strftime('%Y-%m-%d'),
             observed.strftime('%b %d, %Y'), observed.strftime('%b %d, %Y').replace(' 0', ' ')}
    if observed > as_of or len(values) != 1 or not labels.issubset(dates):
        raise ValueError('Inconsistent FRED observation')
    value = values.pop()
    if abs(value) >= 1e12:
        raise ValueError('Invalid FRED value')
    return observed, value


def collect(now=None, opener=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Timezone required')
    result={'retrieved_at_utc':now.isoformat(),'provider':'Federal Reserve Bank of St. Louis (FRED)',
            'release_dates_verified':False,'series':{},'errors':{},
            'warning':'FRED observation dates are NOT verified publication dates; no Weekly Regime score is derived.'}
    for factor,(sid,label,unit) in SERIES.items():
        try:
            day, value, url = read_series(sid, now, opener or urllib.request.urlopen)
            result['series'][factor]={'series_id':sid,'indicator':label,'value':value,'unit':unit,
                'observation_date':day.isoformat(),'retrieved_at_utc':now.isoformat(),
                'source_url':url,'publication_date':None,'publication_date_verified':False,
                'status':'CONTEXT_ONLY_RELEASE_DATE_UNVERIFIED'}
        except (OSError,ValueError,TimeoutError) as e:
            result['errors'][factor]=str(e)
    result['status']='CONTEXT_PARTIAL' if result['series'] else 'CONTEXT_UNAVAILABLE'
    if len(result['series'])==len(SERIES):result['status']='CONTEXT_COLLECTED_UNSCORED'
    return result

def run(path='docs/macro_context.json', receipt_path='docs/macro_collection_health.json', collector=None):
    result=(collector or collect)()
    # Always record the attempted collection, including failures.
    write_json_atomic(receipt_path,receipt(result,len(SERIES)))
    # Preserve the last successful or partial snapshot if the network is unavailable.
    if result.get('series'):
        from macro_snapshot_merge import merge
        try:
            previous=json.loads(Path(path).read_text())
        except (OSError, ValueError):
            previous={}
        write_json_atomic(path,merge(previous,result))
    return result

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
