"""Collect dated macro histories and BLS schedule; no trade signals or live futures."""
import csv, io, json, math, os, re, urllib.request
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
IDS = 'INDPRO CPIAUCSL CPILFESL PCEPI PCEPILFE PAYEMS UNRATE GDPC1 PCEC96 DGS2 DGS10 DFII10 T10YIE BAMLH0A0HYM2 BAMLC0A0CM WALCL WRESBAL WTREGEN RRPONTSYD SOFR IORB NFCI VIXCLS SP500 NASDAQ100 DTWEXBGS DCOILWTICO'.split()
def read(url):
    req=urllib.request.Request(url,headers={'User-Agent':'EasyMoneyResearchDesk/2'})
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read(3000001)
    if len(raw)>3000000: raise ValueError('Response size limit')
    return raw.decode('utf-8-sig')
def parse_csv(raw,sid,today):
    r=csv.DictReader(io.StringIO(raw)); fields=r.fieldnames or []
    dc=next((f for f in ['observation_date','DATE'] if f in fields),None)
    if not dc or sid not in fields:raise ValueError('Unexpected CSV schema')
    rows={}
    for v in r:
        try:
            d=datetime.strptime(v[dc],'%Y-%m-%d').date().isoformat(); n=float(v[sid])
            if d<=today and math.isfinite(n):rows[d]=n
        except (ValueError,TypeError,KeyError):continue
    if not rows:raise ValueError('No observations')
    return sorted([d,v] for d,v in rows.items())[-18:]
def parse_calendar(raw):
    raw=re.sub(r'\r?\n[ \t]','',raw); events=[]
    names={'Employment Situation','Consumer Price Index','Producer Price Index','Job Openings and Labor Turnover Survey'}
    for chunk in raw.split('BEGIN:VEVENT')[1:]:
        dt=re.search(r'DTSTART;TZID=(?:US-Eastern|America/New_York):(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})',chunk)
        name=re.search(r'^SUMMARY:([^\r\n]+)',chunk,re.M)
        if dt and name and name[1].strip() in names:
            y,m,d,h,mi=dt.groups();events.append(dict(day=f'{y}-{m}-{d}',time=f'{h}:{mi}',name=name[1].strip()))
    if not events:raise ValueError('No supported BLS events')
    return sorted(events,key=lambda e:(e['day'],e['time'],e['name']))
def fred(sid,today,now):
    key=os.getenv('FRED_API_KEY')
    if key:
        params=dict(series_id=sid,file_type='json',sort_order='desc',observation_end=today,limit=40)
        public='https://api.stlouisfed.org/fred/series/observations?'+urlencode(params)
        try:
            result=json.loads(read(public+'&'+urlencode(dict(api_key=key))))
            raw='observation_date,'+sid+'\n'+'\n'.join(str(r['date'])+','+str(r['value']) for r in result['observations'])
            return parse_csv(raw,sid,today),public
        except Exception:
            # Exception URLs may contain a key. Never persist the original exception.
            pass
    public=f'https://fred.stlouisfed.org/graph/fredgraph.csv?cosd={(now-timedelta(days=480)).date().isoformat()}&id={sid}'
    return parse_csv(read(public),sid,today),public

def collect(now=None):
    now=now or datetime.now(timezone.utc); checked=now.isoformat();today=now.date().isoformat()
    out=dict(schema_version=1,attempted_at=checked,series={},errors={},calendar=None,live_futures_verified=False)
    def one(sid):
        try:
            rows,url=fred(sid,today,now)
            return sid,dict(rows=rows,checked=checked,kind='hosted collection',source=url),None
        except Exception as e:return sid,None,type(e).__name__+': collection failed'
    with ThreadPoolExecutor(max_workers=6) as pool:
        for sid,value,error in pool.map(one,IDS):
            if error:out['errors'][sid]=error
            else:out['series'][sid]=value
    try:out['calendar']=dict(events=parse_calendar(read('https://www.bls.gov/schedule/news_release/bls.ics')),kind='hosted collection',checked=checked,source='https://www.bls.gov/schedule/news_release/bls.ics')
    except Exception as e:out['errors']['calendar']=type(e).__name__+': '+str(e)[:150]
    out['status']='COMPLETE' if len(out['series'])==len(IDS) and out['calendar'] else 'PARTIAL'
    return out
if __name__=='__main__':
    out=collect(); p=Path('docs/desk_evidence.json');p.parent.mkdir(exist_ok=True)
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2));tmp.replace(p)
    print(json.dumps({'status':out['status'],'series':len(out['series']),'errors':out['errors']}))
