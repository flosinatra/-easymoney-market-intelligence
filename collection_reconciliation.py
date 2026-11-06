"""Reconcile latest collection attempt against retained snapshot; no stale success claims."""
from datetime import datetime, timezone


def parse_time(value):
    try:
        t = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return t if t.tzinfo is not None else None
    except (TypeError, ValueError, AttributeError):
        return None


def reconcile(snapshot, receipt, now=None, freshness_hours=48):
    now = now or datetime.now(timezone.utc)
    attempted = parse_time(receipt.get('attempted_at_utc')) if isinstance(receipt, dict) else None
    captured = parse_time(snapshot.get('retrieved_at_utc')) if isinstance(snapshot, dict) else None
    outcome = receipt.get('collection_status', 'UNKNOWN') if isinstance(receipt, dict) else 'UNKNOWN'
    report = {'latest_attempt_status': outcome, 'latest_attempt_utc': attempted.isoformat() if attempted else None,
              'snapshot_utc': captured.isoformat() if captured else None,
              'snapshot_age_hours': None, 'snapshot_status': 'UNVERIFIED',
              'latest_attempt_produced_snapshot': False, 'latest_attempt_success': False,
              'warnings': []}
    if not captured or captured > now:
        report['warnings'].append('No valid retained snapshot timestamp')
    else:
        age = (now - captured).total_seconds() / 3600
        report['snapshot_age_hours'] = round(age, 2)
        report['snapshot_status'] = 'CURRENT_CONTEXT_ONLY' if age <= freshness_hours else 'STALE_CONTEXT_ONLY'
    if not attempted or attempted > now:
        report['warnings'].append('Latest collection attempt timestamp missing or invalid')
    else:
        report['latest_attempt_success'] = outcome in ('COMPLETE', 'PARTIAL')
        report['latest_attempt_produced_snapshot'] = (report['latest_attempt_success'] and captured is not None
            and abs((captured - attempted).total_seconds()) < 1)
        if outcome == 'FAILED':
            report['warnings'].append('Latest collection failed; retained snapshot is not new evidence')
        if report['latest_attempt_success'] and not report['latest_attempt_produced_snapshot']:
            report['warnings'].append('Collection receipt and retained snapshot timestamps do not match')
    if report['snapshot_status'] == 'STALE_CONTEXT_ONLY':
        report['warnings'].append('Retained snapshot exceeds freshness threshold')
    return report
