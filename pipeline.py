"""Single deterministic build of derived reports from already-collected evidence.
Never downloads data, invents missing scores, or changes workbook definitions.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from treasury_macro_bridge import merge
from macro_factor_evidence import assemble
from weekly_regime import assess
from weekly_regime_evidence import build as rates_packet
from macro_context_integrity import validate as validate_macro_context
from collection_reconciliation import reconcile

def load(path, default):
    try:
        value=json.loads(Path(path).read_text())
        return value if isinstance(value,dict) else default
    except (OSError,ValueError):
        return default

def write(path, value):
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix(target.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(target)

def run(root='docs', now=None):
    root=Path(root);now=now or datetime.now(timezone.utc)
    treasury=load(root/'treasury.json',{})
    existing=load(root/'macro_observations.json',{})
    combined=merge(treasury,existing,now)
    # Never persist a fabricated publication date as a verified release date.
    # The Treasury bridge flags this metadata explicitly for downstream consumers.
    evidence=assemble(combined,now.date())
    weekly=assess(load(root/'weekly_regime_input.json',{}))
    rates=rates_packet(treasury,now)
    macro_context=validate_macro_context(load(root/'macro_context.json',{}),now)
    collection_health=load(root/'macro_collection_health.json',{})
    collection_reconciliation=reconcile(load(root/'macro_context.json',{}),collection_health,now)
    status={'as_of_utc':now.isoformat(),'pipeline':'REPORTS_BUILT',
            'treasury_status':rates['status'],
            'macro_context_status':macro_context['status'],
            'macro_context_available_factors':macro_context['available_factors'],
            'factor_evidence_status':evidence['status'],
            'weekly_regime_status':weekly['gate_result'],
            'automated_macro_score_available':False,
            'live_market_data_verified':False,
            'collector_run_verified':collection_reconciliation['latest_attempt_produced_snapshot'],
            'macro_collection_reconciliation':collection_reconciliation,
            'macro_collection_status':collection_health.get('collection_status','UNKNOWN'),
            'macro_collection_errors':collection_health.get('errors',{}),
            'source_note':'No 1–5 macro score is inferred from Treasury observations.'}
    for name,data in [('macro_observations.json',combined),('macro_factor_evidence.json',evidence),
                      ('weekly_regime_rates_evidence.json',rates),
                      ('weekly_regime_assessment.json',weekly),('macro_context_integrity.json',macro_context),('pipeline_status.json',status)]:
        write(root/name,data)
    return status

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
