"""Read-only field-level audit coverage; never equate source mapping with gate passage."""
import csv
import json
from collections import Counter
from pathlib import Path
from treasury_yields import workbook_yields

GATES = ('Cross-Asset Confirmation', 'Weekly Regime', 'Futures Translation', 'Options Translation', 'Pre-Trade Gate')
# Explicitly mapped workbook fields only. These are DAILY par yields, not live quotes.
TREASURY_FIELDS = {'US30Y Yield':'30-year', 'US10Y Yield':'10-year', 'US05Y Yield':'5-year', 'US02Y Yield':'2-year', 'US01Y Yield':'1-year', 'US03M Yield':'3-month'}

def evaluate(matrix_path, treasury_path=None):
    with open(matrix_path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    treasury = None
    if treasury_path and Path(treasury_path).exists():
        try:
            treasury = json.loads(Path(treasury_path).read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    result = {'version':'0.9', 'purpose':'Workbook field coverage, not trading signals', 'gates':[], 'journal':None,
              'treasury_observation_date': treasury.get('observation_date') if isinstance(treasury,dict) else None,
              'live_market_data_verified':False, 'all_gates_complete':False}
    for name in (*GATES,'Trade Review'):
        fields=[]
        for row in rows:
            if row['Worksheet'] != name: continue
            original=row['Original field'].strip()
            status=row['Verification status']
            item={'cell':row['Header cell'],'field':original,'audit_status':status,'evidence_status':'NOT_VERIFIED', 'value':None}
            if name=='Cross-Asset Confirmation' and original in TREASURY_FIELDS and isinstance(treasury,dict):
                y=workbook_yields(treasury.get('yields_percent',{}))
                if isinstance(y,dict) and isinstance(y.get(TREASURY_FIELDS[original]),(float,int)) and treasury.get('observation_date') and treasury.get('retrieved_at_utc'):
                    item.update(evidence_status='DAILY_OBSERVATION_ONLY',value=y[TREASURY_FIELDS[original]])
            fields.append(item)
        gate={'name':name,'field_count':len(fields),'verified_daily_observations':sum(f['evidence_status']=='DAILY_OBSERVATION_ONLY' for f in fields),
              'audit_status_counts':dict(Counter(f['audit_status'] for f in fields)), 'gate_result':'NOT_ASSESSED', 'fields':fields}
        if name=='Trade Review': result['journal']=gate
        else: result['gates'].append(gate)
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--matrix',default='source_matrix.csv')
    parser.add_argument('--treasury',default='docs/treasury.json')
    parser.add_argument('--out',default='docs/gate_coverage.json')
    a=parser.parse_args()
    result=evaluate(a.matrix,a.treasury)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Mapped',sum(g['field_count'] for g in result['gates'])+result['journal']['field_count'],'fields; no gates passed')
