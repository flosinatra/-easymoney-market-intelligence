"""Durable collection receipt; never infer success from script exit alone."""
import json
from datetime import datetime, timezone
from pathlib import Path


def receipt(result, expected=4):
    series=result.get('series',{}) if isinstance(result,dict) else {}
    errors=result.get('errors',{}) if isinstance(result,dict) else {}
    count=len(series)
    return {'attempted_at_utc':result.get('retrieved_at_utc') if isinstance(result,dict) else None,
            'collection_status':'COMPLETE' if count==expected else 'PARTIAL' if count else 'FAILED',
            'collected_series':count,'expected_series':expected,
            'failed_factors':sorted(errors), 'errors':errors,
            'release_dates_verified':False,'macro_scores_available':False}


def write_json_atomic(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    tmp.replace(path)
