"""Independent source collection with honest source-specific receipts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from publish_treasury import run as treasury_run
from collect_macro_context import run as macro_run
from pipeline import run as pipeline_run
from collection_health import write_json_atomic


def execute(root='docs', treasury_collector=None, macro_collector=None, now=None):
    started_at = now or datetime.now(timezone.utc)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    outcomes = {'attempted_at_utc': started_at.isoformat()}
    try:
        treasury = (treasury_collector or (lambda: treasury_run(out=str(root/'treasury.json'), history=str(root/'history'))))()
        # A collector returning None is not evidence of a successful download.
        if isinstance(treasury, dict) and treasury.get('observation_date') and treasury.get('retrieved_at_utc'):
            outcomes['treasury'] = 'COLLECTION_SUCCEEDED'
            outcomes['treasury_observation_date'] = treasury['observation_date']
        else:
            outcomes['treasury'] = 'RESULT_UNVERIFIED'
    except Exception as exc:
        outcomes['treasury'] = 'COLLECTION_FAILED'
        outcomes['treasury_error'] = type(exc).__name__ + ': ' + str(exc)[:300]
    try:
        macro = (macro_collector or (lambda: macro_run(path=str(root/'macro_context.json'), receipt_path=str(root/'macro_collection_health.json'))))()
        series = macro.get('series', {}) if isinstance(macro, dict) else {}
        if not isinstance(series, dict):
            series = {}
        outcomes['macro'] = 'COMPLETE' if len(series) == 4 else 'PARTIAL' if series else 'COLLECTION_FAILED_OR_UNVERIFIED'
        outcomes['macro_collected_series'] = len(series)
        outcomes['macro_failed_factors'] = sorted(macro.get('errors', {})) if isinstance(macro, dict) else []
    except Exception as exc:
        outcomes['macro'] = 'COLLECTION_FAILED'
        outcomes['macro_error'] = type(exc).__name__ + ': ' + str(exc)[:300]
    try:
        pipeline_run(root=root, now=now or datetime.now(timezone.utc))
        outcomes['pipeline'] = 'REPORTS_BUILT_NOT_GATE_PASSED'
    except Exception as exc:
        outcomes['pipeline'] = 'REPORTS_FAILED'
        outcomes['pipeline_error'] = type(exc).__name__ + ': ' + str(exc)[:300]
    write_json_atomic(root/'hosted_collection_receipt.json', outcomes)
    return outcomes

if __name__ == '__main__':
    print(json.dumps(execute(), indent=2))
