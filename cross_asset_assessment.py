"""Limited Treasury curve evidence; no cross-asset gate passage or regime scoring."""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from treasury_yields import workbook_yields

PAIRS = [('10Y minus 2Y', '10-year', '2-year'), ('10Y minus 3M', '10-year', '3-month')]

def assess(snapshot, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    result = {'version': '0.10', 'gate': 'Cross-Asset Confirmation', 'gate_result': 'NOT_ASSESSED',
              'execution_status': 'NOT_ASSESSED', 'source': 'U.S. Treasury daily par yields',
              'observation_date': snapshot.get('observation_date'),
              'retrieved_at_utc': snapshot.get('retrieved_at_utc'),
              'curve_spreads_basis_points': {}, 'evidence_status': 'UNVERIFIED',
              'limitations': ['Daily nominal Treasury yields only', 'No real yields, credit, dollar, VIX, commodities or live futures confirmation',
                              'Curve shape is context, not a directional trade signal']}
    try:
        observed = date.fromisoformat(snapshot['observation_date'])
        retrieved = datetime.fromisoformat(snapshot['retrieved_at_utc'].replace('Z', '+00:00'))
        if retrieved.tzinfo is None or as_of.tzinfo is None or observed > as_of.date() or retrieved > as_of:
            raise ValueError('Invalid or future timestamp')
        age = (as_of.date() - observed).days
        if age > 4:
            result['evidence_status'] = 'STALE_DAILY_OBSERVATION'
            return result
        y = workbook_yields(snapshot['yields_percent'])
        for label, long, short in PAIRS:
            a, b = y.get(long), y.get(short)
            if isinstance(a, (int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):
                if 0 <= a <= 30 and 0 <= b <= 30:
                    result['curve_spreads_basis_points'][label] = round((a-b)*100, 1)
        result['evidence_status'] = 'DAILY_CURVE_CONTEXT_ONLY' if result['curve_spreads_basis_points'] else 'INSUFFICIENT_DAILY_DATA'
    except (ValueError, KeyError, TypeError, AttributeError):
        pass
    return result

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--treasury',default='docs/treasury.json');p.add_argument('--out',default='docs/cross_asset_assessment.json');a=p.parse_args()
    try: data=json.loads(Path(a.treasury).read_text())
    except (OSError,ValueError): data={}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(assess(data),indent=2))
    print('Cross-asset gate NOT ASSESSED; curve context only')
