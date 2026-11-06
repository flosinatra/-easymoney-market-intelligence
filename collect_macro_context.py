"""Download public FRED CSV observations for context; never claim release-time verification.

FRED CSV dates are observation dates, not dates the data became public. These
observations are intentionally excluded from scored Weekly Regime evidence.
"""
import csv
import io
import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from collection_health import receipt, write_json_atomic

SERIES = {
    'Growth': ('INDPRO', 'Industrial Production Index', 'index'),
    'Inflation': ('CPIAUCSL', 'Consumer Price Index for All Urban Consumers', 'index'),
    'Credit': ('BAMLH0A0HYM2', 'ICE BofA US High Yield Option-Adjusted Spread', 'percentage points'),
    'Liquidity': ('WALCL', 'Federal Reserve Total Assets', 'millions of USD'),
}
URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={}'

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

def collect(now=None, opener=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Timezone required')
    result={'retrieved_at_utc':now.isoformat(),'provider':'Federal Reserve Bank of St. Louis (FRED)',
            'release_dates_verified':False,'series':{},'errors':{},
            'warning':'FRED observation dates are NOT verified publication dates; no Weekly Regime score is derived.'}
    for factor,(sid,label,unit) in SERIES.items():
        url=URL.format(sid)
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'EasyMoneyResearchCollector/0.17'})
            with (opener or urllib.request.urlopen)(req,timeout=25) as response:
                raw=response.read(3_000_001)
            if len(raw)>3_000_000: raise ValueError('Response too large')
            day,value=parse_series(raw,sid,now.date())
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
