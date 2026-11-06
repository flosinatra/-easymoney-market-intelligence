"""Persistent, append-only-by-hash public evidence archive for verified Treasury snapshots."""
import json
from datetime import datetime
from pathlib import Path


def archive_snapshot(snapshot, root='docs/history'):
    digest = snapshot['source_file_sha256']
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid source hash')
    date = snapshot['observation_date']
    if not isinstance(date, str) or len(date) != 10 or date[4] != '-' or date[7] != '-':
        raise ValueError('Invalid observation date')
    folder = Path(root) / date[:7]
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / f'{date}_{digest[:16]}.json'
    payload = json.dumps(snapshot, indent=2, sort_keys=True)
    if dest.exists():
        archived = json.loads(dest.read_text(encoding='utf-8'))
        if archived == snapshot:
            return str(dest)
        captured = datetime.fromisoformat(snapshot['retrieved_at_utc'].replace('Z', '+00:00'))
        if captured.tzinfo is None or {**archived, 'retrieved_at_utc': snapshot['retrieved_at_utc']} != snapshot:
            raise ValueError('Evidence archive collision')
        return str(dest)
    temp = dest.with_suffix('.tmp')
    temp.write_text(payload, encoding='utf-8')
    temp.replace(dest)
    return str(dest)
