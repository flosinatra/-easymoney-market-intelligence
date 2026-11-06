"""Validate FRED context snapshots without promoting observation dates to release dates."""
from datetime import date, datetime, timezone
from collect_macro_context import SERIES
from macro_snapshot_merge import parse_timestamp


def validate(snapshot, now=None):
    now = now or datetime.now(timezone.utc)
    result = {'status': 'UNVERIFIED', 'retrieved_at_utc': None, 'factors': {},
              'available_factors': 0, 'missing_factors': [],
              'warning': 'FRED observation dates do not establish release timing; no scores derived.'}
    if not isinstance(snapshot, dict):
        return result
    try:
        retrieved = datetime.fromisoformat(snapshot['retrieved_at_utc'].replace('Z', '+00:00'))
        if retrieved.tzinfo is None or retrieved > now or (now-retrieved).total_seconds() > 48*3600:
            result['status'] = 'STALE_OR_INVALID_RETRIEVAL'
            return result
        result['retrieved_at_utc'] = retrieved.isoformat()
    except (KeyError, TypeError, ValueError, AttributeError):
        return result
    for factor, (series_id, _, _) in SERIES.items():
        record = snapshot.get('series', {}).get(factor)
        status = 'MISSING'
        if isinstance(record, dict):
            try:
                record_time = parse_timestamp(record.get('retrieved_at_utc', snapshot['retrieved_at_utc']))
                if record_time is None or record_time > now or (now-record_time).total_seconds() > 48*3600:
                    result['factors'][factor] = 'STALE_OR_INVALID_SERIES'
                    result['missing_factors'].append(factor)
                    continue
                day = date.fromisoformat(record['observation_date'])
                if (record['series_id'] == series_id and day <= now.date()
                        and record.get('publication_date_verified') is False
                        and record.get('publication_date') is None
                        and record.get('status') == 'CONTEXT_ONLY_RELEASE_DATE_UNVERIFIED'
                        and type(record['value']) in (float, int)
                        and float('-inf') < record['value'] < float('inf')):
                    status = 'CONTEXT_ONLY'
                    result['available_factors'] += 1
            except (KeyError, TypeError, ValueError):
                status = 'INVALID'
        if status != 'CONTEXT_ONLY':
            result['missing_factors'].append(factor)
        result['factors'][factor] = status
    result['status'] = ('CONTEXT_AVAILABLE_UNSCORED' if result['available_factors'] == len(SERIES)
                        else 'CONTEXT_PARTIAL_UNSCORED' if result['available_factors'] else 'CONTEXT_UNAVAILABLE')
    return result
