"""Merge successful partial FRED downloads without hiding the age of retained series."""
from datetime import datetime, timezone
from collect_macro_context import SERIES


def parse_timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo else None
    except (AttributeError, ValueError, TypeError):
        return None


def merge(previous, attempt):
    """Use only actual downloaded records as new; retain old rows with their own timestamps."""
    previous = previous if isinstance(previous, dict) else {}
    attempt = attempt if isinstance(attempt, dict) else {}
    fresh = attempt.get('series', {})
    old = previous.get('series', {})
    if not isinstance(fresh, dict): fresh = {}
    if not isinstance(old, dict): old = {}
    if not fresh:
        return previous  # A failed attempt must never change the retained snapshot.
    stamp = parse_timestamp(attempt.get('retrieved_at_utc'))
    if stamp is None:
        return previous
    combined = {}
    for factor, (sid, _, _) in SERIES.items():
        new = fresh.get(factor)
        prior = old.get(factor)
        if isinstance(new, dict) and new.get('series_id') == sid and parse_timestamp(new.get('retrieved_at_utc')) == stamp:
            combined[factor] = dict(new)
        elif isinstance(prior, dict) and prior.get('series_id') == sid and parse_timestamp(prior.get('retrieved_at_utc')):
            combined[factor] = dict(prior)
    output = dict(attempt)
    output['series'] = combined
    output['new_series_count'] = sum(1 for factor in combined if factor in fresh and combined[factor] == fresh[factor])
    output['retained_series_count'] = len(combined) - output['new_series_count']
    output['warning'] = 'Each series has its own retrieval timestamp. Retained rows are NOT newly collected.'
    return output
