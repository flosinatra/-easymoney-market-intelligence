"""Official US Treasury XML feed adapter. Daily observations, not live quotes."""
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from treasury_yields import TENORS

BASE = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml'

def official_url(year_month):
    if len(year_month)!=6 or not year_month.isdigit() or not 1<=int(year_month[4:])<=12:
        raise ValueError('Expected YYYYMM')
    return BASE+'?data=daily_treasury_yield_curve&field_tdr_date_value_month='+year_month

def parse_xml(raw, captured_at=None):
    captured_at = captured_at or datetime.now(timezone.utc)
    root = ET.fromstring(raw)
    entries = []
    for entry in root.iter():
        if entry.tag.split('}')[-1].lower() != 'entry':
            continue
        fields = {}
        for element in entry.iter():
            name=element.tag.split('}')[-1].upper()
            if element.text and element.text.strip():
                fields[name]=element.text.strip()
        date_text=fields.get('NEW_DATE') or fields.get('DATE')
        if not date_text:
            continue
        day=datetime.fromisoformat(date_text.replace('Z','+00:00')).date()
        if day>captured_at.date():
            raise ValueError('Future observation')
        rates={}
        for label,key in TENORS.items():
            tag='BC_'+label.upper().replace(' ','_')
            if label.endswith(' Yr'): tag='BC_'+label.split()[0]+'YEAR'
            if label.endswith(' Mo'): tag='BC_'+label.split()[0]+'MONTH'
            value=fields.get(tag)
            if value in (None,'N/A','ND',''):
                rates[key]=None
            else:
                rate=float(value)
                if not -5<=rate<=30:
                    raise ValueError('Implausible yield')
                rates[key]=rate
        entries.append({'observation_date':day.isoformat(),'yield_percent':rates})
    if not entries:
        raise ValueError('No daily yield observations found')
    dates=[x['observation_date'] for x in entries]
    if len(set(dates))!=len(dates):
        raise ValueError('Duplicate observation')
    entries.sort(key=lambda x:x['observation_date'])
    return {'source':'US Treasury','dataset':'Daily Treasury Par Yield Curve Rates',
            'retrieved_at_utc':captured_at.isoformat(),
            'source_file_sha256':hashlib.sha256(raw).hexdigest(),
            'source_publication_time_verified':False,'intraday_quote':False,
            'status':'historical_daily_evidence_only',
            'latest_observation_date':entries[-1]['observation_date'],
            'observations':entries}

def collect_month(year_month, db_path, opener=None):
    from evidence_store import store_evidence
    url=official_url(year_month)
    req=urllib.request.Request(url,headers={'User-Agent':'EasyMoneyResearchCollector/0.6'})
    with (opener or urllib.request.urlopen)(req,timeout=20) as response:
        raw=response.read(10_000_001)
    if len(raw)>10_000_000: raise ValueError('Oversized response')
    payload=parse_xml(raw)
    payload['source_url']=url
    archive=store_evidence(db_path,payload)
    return {'latest_observation_date':payload['latest_observation_date'],
            'observation_count':len(payload['observations']),'archive':archive,
            'publication_time_verified':False,'live_intraday_data':False}
