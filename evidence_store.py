"""Append-only local evidence archive. No scores, signals, or trading instructions."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = '''CREATE TABLE IF NOT EXISTS evidence (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 source TEXT NOT NULL, dataset TEXT NOT NULL,
 observed_through TEXT, captured_at_utc TEXT NOT NULL,
 stored_at_utc TEXT NOT NULL, content_sha256 TEXT NOT NULL,
 payload_json TEXT NOT NULL,
 UNIQUE(source, dataset, content_sha256)
)'''

def store_evidence(db_path, payload):
    if not isinstance(payload, dict):
        raise ValueError('Evidence must be a JSON object')
    for key in ('source', 'dataset', 'retrieved_at_utc'):
        if not payload.get(key):
            raise ValueError(f'Missing evidence field: {key}')
    captured = datetime.fromisoformat(payload['retrieved_at_utc'].replace('Z', '+00:00'))
    if captured.tzinfo is None:
        raise ValueError('Retrieval time must include timezone')
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)
    digest = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(SCHEMA)
        cur = con.execute('''INSERT OR IGNORE INTO evidence
         (source, dataset, observed_through, captured_at_utc, stored_at_utc, content_sha256, payload_json)
         VALUES (?,?,?,?,?,?,?)''',
         (payload['source'], payload['dataset'], payload.get('latest_observation_date'),
          captured.astimezone(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat(), digest, encoded))
        inserted = cur.rowcount == 1
    return {'stored': inserted, 'sha256': digest}

def list_evidence(db_path):
    if not Path(db_path).exists():
        return []
    with sqlite3.connect(db_path) as con:
        con.execute(SCHEMA)
        return [dict(zip(('source','dataset','observed_through','captured_at_utc','content_sha256'), row))
                for row in con.execute('''SELECT source,dataset,observed_through,captured_at_utc,content_sha256
                                          FROM evidence ORDER BY id DESC''')]
